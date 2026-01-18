class LR1Parser:
    def __init__(self):
        # Define the grammar G=(N,T,S,P)
        self.N = ['E', 'T', 'F']  # Non-terminals
        self.T = ['a', '+', '-', '*', '/', '(', ')']  # Terminals (including 'a' for identifiers)
        self.S = 'E'  # Start symbol
        # Productions P with numbers
        self.P = {
            1: ('E', 'E+T'),
            2: ('E', 'T'), 
            3: ('T', 'T*F'),
            4: ('T', 'F'),
            5: ('F', '(E)'),
            6: ('F', 'a') 
        }
        
        # Augmented grammar with S' -> S
        self.augmented_P = {0: ("S'", 'E')}
        self.augmented_P.update(self.P)
        
        self.itemsets = []  # Canonical collection of LR(1) itemsets
        self.parsing_table = {}  # LR(1) parsing table
        self.first_sets = {}  # FIRST sets for non-terminals
        
    def compute_first_sets(self):
        """Compute FIRST sets for all non-terminals"""
        # Initialize FIRST sets
        for nt in self.N:
            self.first_sets[nt] = set()
        for t in self.T:
            self.first_sets[t] = {t}
        
        # Add epsilon for completeness (though not used in this grammar)
        self.first_sets['ε'] = {'ε'}
        
        changed = True
        while changed:
            changed = False
            for prod_num, (left, right) in self.P.items():
                # For each production left -> right
                symbols = list(right)
                
                # Check if all symbols can derive epsilon (not in this grammar)
                all_epsilon = True
                for symbol in symbols:
                    if symbol in self.T:  # Terminal
                        # Add terminal to FIRST(left)
                        if symbol not in self.first_sets[left]:
                            self.first_sets[left].add(symbol)
                            changed = True
                        break
                    else:  # Non-terminal
                        # Add FIRST(non_terminal) to FIRST(left)
                        first_of_symbol = self.first_sets.get(symbol, set())
                        new_terminals = first_of_symbol - self.first_sets[left]
                        if new_terminals:
                            self.first_sets[left].update(new_terminals)
                            changed = True
                        # If this non-terminal doesn't contain epsilon, stop
                        if 'ε' not in first_of_symbol:
                            break
    
    def first_of_string(self, string, lookahead):
        """Compute FIRST of a string of symbols"""
        if not string:
            return {lookahead}
        
        result = set()
        all_epsilon = True
        
        for symbol in string:
            if symbol in self.T:  # Terminal
                result.add(symbol)
                all_epsilon = False
                break
            else:  # Non-terminal
                first = self.first_sets.get(symbol, set())
                # Remove epsilon if present
                if 'ε' in first:
                    first = first - {'ε'}
                result.update(first)
                if 'ε' not in self.first_sets.get(symbol, set()):
                    all_epsilon = False
                    break
        
        if all_epsilon:
            result.add(lookahead)
            
        return result
    
    def closure(self, items):
        """Compute closure of a set of LR(1) items"""
        closure_set = set(items)
        changed = True
        
        while changed:
            changed = False
            new_items = set()
            
            for item in list(closure_set):
                # item format: (prod_num, dot_pos, lookahead)
                prod_num, dot_pos, lookahead = item
                left, right = self.augmented_P[prod_num]
                symbols = list(right)
                
                # If dot is at the end, nothing to do
                if dot_pos >= len(symbols):
                    continue
                
                next_symbol = symbols[dot_pos]
                
                # If next symbol is a non-terminal, we need to add its productions
                if next_symbol in self.N:
                    # Get the remaining symbols after the next_symbol
                    remaining_symbols = symbols[dot_pos + 1:]
                    
                    # Compute lookaheads for the new items
                    lookaheads = self.first_of_string(remaining_symbols, lookahead)
                    
                    # Add all productions of this non-terminal with each lookahead
                    for new_prod_num, (new_left, new_right) in self.augmented_P.items():
                        if new_left == next_symbol:
                            for la in lookaheads:
                                new_item = (new_prod_num, 0, la)  # Dot at beginning
                                if new_item not in closure_set and new_item not in new_items:
                                    new_items.add(new_item)
                                    changed = True
            
            closure_set.update(new_items)
        
        return closure_set
    
    def goto(self, itemset, symbol):
        """Compute GOTO for an itemset and symbol"""
        new_items = set()
        
        for item in itemset:
            prod_num, dot_pos, lookahead = item
            left, right = self.augmented_P[prod_num]
            symbols = list(right)
            
            # If dot is before our symbol, move dot past it
            if dot_pos < len(symbols) and symbols[dot_pos] == symbol:
                new_item = (prod_num, dot_pos + 1, lookahead)
                new_items.add(new_item)
        
        # Return closure of the new items
        return self.closure(new_items) if new_items else set()
    
    def itemsets_are_equal(self, set1, set2):
        """Check if two itemsets are equal"""
        return set1 == set2
    
    def build_canonical_collection(self):
        #"""Build the canonical collection of LR(1) itemsets"""
        #print("Building canonical collection of LR(1) itemsets...")
        
        # Start with initial itemset I0
        initial_item = (0, 0, '$')  # (S' -> .E, $)
        I0 = self.closure({initial_item})
        self.itemsets = [I0]
        
        # Use queue to process itemsets
        queue = [0]
        processed = set()
        
        while queue:
            current_idx = queue.pop(0)
            if current_idx in processed:
                continue
            processed.add(current_idx)
            
            current_itemset = self.itemsets[current_idx]
            print(f"\nProcessing I{current_idx} ({len(current_itemset)} items):")
            
            # Display items in this itemset
            for item in sorted(current_itemset):
                prod_num, dot_pos, lookahead = item
                left, right = self.augmented_P[prod_num]
                symbols = list(right)
                
                # Create dotted production string
                dotted_right = ' '.join(symbols[:dot_pos] + ['.'] + symbols[dot_pos:])
                print(f"  [{left} -> {dotted_right}, {lookahead}]")
            
            # Try all symbols (terminals and non-terminals)
            all_symbols = self.T + self.N
            
            for symbol in all_symbols:
                goto_set = self.goto(current_itemset, symbol)
                
                if goto_set:
                    # Check if this itemset already exists
                    found_idx = -1
                    for idx, existing_set in enumerate(self.itemsets):
                        if self.itemsets_are_equal(existing_set, goto_set):
                            found_idx = idx
                            break
                    
                    if found_idx == -1:
                        # New itemset
                        found_idx = len(self.itemsets)
                        self.itemsets.append(goto_set)
                        queue.append(found_idx)
                        #print(f"    I{current_idx} --{symbol}--> I{found_idx} (NEW)")
                    # else:
                    #     print(f"    I{current_idx} --{symbol}--> I{found_idx} (EXISTING)")
        
        print(f"\nCanonical collection complete: {len(self.itemsets)} states generated")
    
    def build_parsing_table(self):
        """Build LR(1) parsing table from canonical collection"""
        print("\nBuilding LR(1) parsing table...")
        
        # Initialize empty table
        for i in range(len(self.itemsets)):
            self.parsing_table[i] = {}
            for terminal in self.T + ['$']:
                self.parsing_table[i][terminal] = ''
            for non_terminal in self.N:
                self.parsing_table[i][non_terminal] = ''
        
        # Fill the table using standard LR(1) algorithm
        for i, itemset in enumerate(self.itemsets):
            #print(f"\nProcessing I{i} for parsing table:")
            
            # Process each item in the itemset
            for item in itemset:
                prod_num, dot_pos, lookahead = item
                left, right = self.augmented_P[prod_num]
                symbols = list(right)
                
                # Case 1: Dot is not at the end (shift or goto)
                if dot_pos < len(symbols):
                    next_symbol = symbols[dot_pos]
                    goto_set = self.goto(itemset, next_symbol)
                    
                    if goto_set:
                        goto_index = self.itemsets.index(goto_set)
                        
                        if next_symbol in self.T:  # Terminal - shift action
                            action = f's{goto_index}'
                            current_action = self.parsing_table[i][next_symbol]
                            if current_action and current_action != action:
                                print(f"    CONFLICT at I{i},{next_symbol}: {current_action} vs {action}")
                            else:
                                self.parsing_table[i][next_symbol] = action
                                print(f"    ACTION[{i},{next_symbol}] = {action}")
                        else:  # Non-terminal - goto action
                            current_goto = self.parsing_table[i][next_symbol]
                            if current_goto and current_goto != str(goto_index):
                                print(f"    GOTO conflict at I{i},{next_symbol}: {current_goto} vs {goto_index}")
                            else:
                                self.parsing_table[i][next_symbol] = str(goto_index)
                                print(f"    GOTO[{i},{next_symbol}] = {goto_index}")
                
                # Case 2: Dot is at the end (reduce or accept)
                else:
                    if prod_num == 0 and lookahead == '$':  # S' -> E.
                        self.parsing_table[i][lookahead] = 'acc'
                        print(f"    ACTION[{i},{lookahead}] = acc")
                    else:  # Reduce action
                        # Find the original production number (excluding augmented)
                        original_prod_num = prod_num
                        action = f'r{original_prod_num}'
                        
                        current_action = self.parsing_table[i][lookahead]
                        if current_action and current_action != action:
                            print(f"    REDUCE CONFLICT at I{i},{lookahead}: {current_action} vs {action}")
                        else:
                            self.parsing_table[i][lookahead] = action
                            prod_left, prod_right = self.P[original_prod_num]
                            print(f"    ACTION[{i},{lookahead}] = {action} (reduce by {prod_left}->{prod_right})")
    
    def display_parsing_table(self):
        """Display the LR(1) parsing table in a readable format"""
        print("\n" + "="*80)
        print("LR(1) PARSING TABLE - ALGORITHMICALLY GENERATED")
        print("="*80)
        print("Grammar: G=(N,T,S,P) where:")
        print(f"  N = {self.N}")
        print(f"  T = {self.T}")
        print(f"  S = {self.S}")
        print("  P = {")
        for num, (left, right) in self.P.items():
            print(f"    {num}: {left} -> {right}")
        print("  }")
        print("="*80)
        
        # Define column order
        terminals_order = ['a', '+', '-', '*', '/', '(', ')', '$']
        non_terminals_order = ['E', 'T', 'F']
        
        # Header
        print(f"{'State':<6}", end="")
        for term in terminals_order:
            print(f"{term:<6}", end="")
        print("|", end="")
        for nt in non_terminals_order:
            print(f"{nt:<6}", end="")
        print()
        print("-" * (6 + 6*len(terminals_order) + 1 + 6*len(non_terminals_order)))
        
        # Table rows
        for state in range(len(self.itemsets)):
            print(f"{state:<6}", end="")
            
            # Action part (terminals)
            for term in terminals_order:
                action = self.parsing_table[state].get(term, '')
                print(f"{action:<6}", end="")
            
            print("|", end="")
            
            # Goto part (non-terminals)
            for nt in non_terminals_order:
                goto = self.parsing_table[state].get(nt, '')
                print(f"{goto:<6}", end="")
            
            print()
    
    def parse_input(self, input_string):
        """Parse an input string using the generated LR(1) parsing table"""
        print(f"\nParsing input: {input_string}")
        
        # Initialize stack and input
        stack = [0]  # Start with state 0
        input_list = list(input_string) + ['$']
        position = 0
        
        print(f"{'Step':<4} {'Stack':<30} {'Input':<20} {'Action':<10}")
        print("-" * 70)
        
        step = 0
        while True:
            current_state = stack[-1]
            current_input = input_list[position]
            
            print(f"{step:<4} {str(stack):<30} {''.join(input_list[position:]):<20}", end="")
            
            action = self.parsing_table[current_state].get(current_input, '')
            
            if not action:
                print(f"{'ERROR':<10}")
                print("No action defined - parsing failed!")
                return False
            
            if action == 'acc':
                print(f"{'ACCEPT':<10}")
                print("Input successfully parsed!")
                return True
            
            elif action.startswith('s'):  # Shift
                next_state = int(action[1:])
                stack.append(current_input)  # Push symbol
                stack.append(next_state)     # Push state
                position += 1
                print(f"shift {next_state:<4}")
            
            elif action.startswith('r'):  # Reduce
                prod_num = int(action[1:])
                left, right = self.P[prod_num]
                rhs_length = len(right)
                
                # Pop 2*rhs_length elements (symbols and states)
                stack = stack[:-2 * rhs_length]
                
                # Get the state after popping
                goto_state = int(self.parsing_table[stack[-1]][left])
                stack.append(left)        # Push left-hand side
                stack.append(goto_state)  # Push goto state
                
                print(f"reduce {prod_num:<3}")
            
            step += 1
            if step > 50:  # Safety limit
                print("Parsing steps limit exceeded!")
                return False

def main():
    """Main function to demonstrate LR(1) parser"""
    print("LR(1) PARSING TABLE GENERATOR")
    print("="*50)
    
    # Create parser
    parser = LR1Parser()
    
    # Step 1: Compute FIRST sets
    print("\n1. COMPUTING FIRST SETS...")
    parser.compute_first_sets()
    print("FIRST sets computed:")
    for symbol in parser.N:
        print(f"  FIRST({symbol}) = {sorted(parser.first_sets[symbol])}")
    
    # Step 2: Build canonical collection
    print("\n2. BUILDING CANONICAL COLLECTION...")
    parser.build_canonical_collection()
    
    # Step 3: Build parsing table
    print("\n3. BUILDING PARSING TABLE...")
    parser.build_parsing_table()
    
    # Step 4: Display the table
    parser.display_parsing_table()
    
    # Step 5: Test parsing
    print("\n4. TESTING PARSER...")
    test_inputs = [
        "a+a*a",
        "(a+a)*a", 
        "a*a+a",
        "a"
    ]
    
    for test_input in test_inputs:
        print(f"\n{'='*50}")
        success = parser.parse_input(test_input)
        if success:
            print(f" '{test_input}' is valid")
        else:
            print(f" '{test_input}' is invalid")

if __name__ == "__main__":
    main()