class LR1Translator:
    def __init__(self):
        self.N = ['E', 'T', 'F'] 
        self.T = ['a', '+', '-', '*', '/', '(', ')']
        self.S = 'E'
        
        self.P = {
            1: ('E', 'E+T'),
            11: ('E', 'E-T'),
            2: ('E', 'T'), 
            3: ('T', 'T*F'),
            31: ('T', 'T/F'),
            4: ('T', 'F'),
            5: ('F', '(E)'),
            6: ('F', 'a'),
            51: ('F', '-(E)')
        }
        
        self.augmented_P = {0: ("S'", 'E')}
        self.augmented_P.update(self.P)
        
        self.itemsets = []
        self.parsing_table = {}
        self.first_sets = {}
        
        self.temp_counter = 0
        self.intermediate_code = []
        
    def newtemp(self):
        """Generate a new temporary variable"""
        self.temp_counter += 1
        return f"t{self.temp_counter}"
    
    def emit(self, code):
        """Emit intermediate code"""
        self.intermediate_code.append(code)
    
    def compute_first_sets(self):
        """Compute FIRST sets for all non-terminals"""
        for nt in self.N:
            self.first_sets[nt] = set()
        for t in self.T:
            self.first_sets[t] = {t}
        
        self.first_sets['ε'] = {'ε'}
        
        changed = True
        while changed:
            changed = False
            for prod_num, (left, right) in self.P.items():
                symbols = list(right)
                
                for symbol in symbols:
                    if symbol in self.T:
                        if symbol not in self.first_sets[left]:
                            self.first_sets[left].add(symbol)
                            changed = True
                        break
                    else:
                        first_of_symbol = self.first_sets.get(symbol, set())
                        new_terminals = first_of_symbol - self.first_sets[left]
                        if new_terminals:
                            self.first_sets[left].update(new_terminals)
                            changed = True
                        if 'ε' not in first_of_symbol:
                            break
    
    def first_of_string(self, string, lookahead):
        """Compute FIRST of a string of symbols"""
        if not string:
            return {lookahead}
        
        result = set()
        all_epsilon = True
        
        for symbol in string:
            if symbol in self.T:
                result.add(symbol)
                all_epsilon = False
                break
            else:
                first = self.first_sets.get(symbol, set())
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
        closure_set = set(items)
        changed = True
        
        while changed:
            changed = False
            new_items = set()
            
            for item in list(closure_set):
                prod_num, dot_pos, lookahead = item
                left, right = self.augmented_P[prod_num]
                symbols = list(right)
                
                if dot_pos >= len(symbols):
                    continue
                
                next_symbol = symbols[dot_pos]
                
                if next_symbol in self.N:
                    remaining_symbols = symbols[dot_pos + 1:]
                    lookaheads = self.first_of_string(remaining_symbols, lookahead)
                    
                    for new_prod_num, (new_left, new_right) in self.augmented_P.items():
                        if new_left == next_symbol:
                            for la in lookaheads:
                                new_item = (new_prod_num, 0, la)
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
            
            if dot_pos < len(symbols) and symbols[dot_pos] == symbol:
                new_item = (prod_num, dot_pos + 1, lookahead)
                new_items.add(new_item)
        
        return self.closure(new_items) if new_items else set()
    
    def build_canonical_collection(self):
        """Build the canonical collection of LR(1) itemsets"""
        initial_item = (0, 0, '$')
        I0 = self.closure({initial_item})
        self.itemsets = [I0]
        
        queue = [0]
        processed = set()
        
        while queue:
            current_idx = queue.pop(0)
            if current_idx in processed:
                continue
            processed.add(current_idx)
            
            current_itemset = self.itemsets[current_idx]
            all_symbols = self.T + self.N
            
            for symbol in all_symbols:
                goto_set = self.goto(current_itemset, symbol)
                
                if goto_set:
                    found_idx = -1
                    for idx, existing_set in enumerate(self.itemsets):
                        if existing_set == goto_set:
                            found_idx = idx
                            break
                    
                    if found_idx == -1:
                        found_idx = len(self.itemsets)
                        self.itemsets.append(goto_set)
                        queue.append(found_idx)
    
    def build_parsing_table(self):
        """Build LR(1) parsing table from canonical collection"""
        for i in range(len(self.itemsets)):
            self.parsing_table[i] = {}
            for terminal in self.T + ['$']:
                self.parsing_table[i][terminal] = ''
            for non_terminal in self.N:
                self.parsing_table[i][non_terminal] = ''
        
        for i, itemset in enumerate(self.itemsets):
            for item in itemset:
                prod_num, dot_pos, lookahead = item
                left, right = self.augmented_P[prod_num]
                symbols = list(right)
                
                if dot_pos < len(symbols):
                    next_symbol = symbols[dot_pos]
                    goto_set = self.goto(itemset, next_symbol)
                    
                    if goto_set:
                        goto_index = self.itemsets.index(goto_set)
                        
                        if next_symbol in self.T:
                            action = f's{goto_index}'
                            self.parsing_table[i][next_symbol] = action
                        else:
                            self.parsing_table[i][next_symbol] = str(goto_index)
                else:
                    if prod_num == 0 and lookahead == '$':
                        self.parsing_table[i][lookahead] = 'acc'
                    else:
                        action = f'r{prod_num}'
                        self.parsing_table[i][lookahead] = action
    
    def translate_input(self, input_string):
        """Translate input string to intermediate code"""
        self.temp_counter = 0
        self.intermediate_code = []
        
        stack = [0] 
        attr_stack = []
        input_list = list(input_string) + ['$']
        position = 0
        
        identifier_counter = 0
        
        step = 0
        while True:
            current_state = stack[-1]
            current_input = input_list[position]
            
            action = self.parsing_table[current_state].get(current_input, '')
            
            if not action:
                return None
            
            if action == 'acc':
                return self.intermediate_code
            
            elif action.startswith('s'): 
                next_state = int(action[1:])
                stack.append(next_state)
                
                if current_input == 'a':
                    identifier_counter += 1
                    identifier = f"a{identifier_counter}"
                    attr_stack.append(identifier)
                
                position += 1
            
            elif action.startswith('r'):
                prod_num = int(action[1:])
                left, right = self.P[prod_num]
                rhs_length = len(right)
                
                stack = stack[:-rhs_length]
                
                if prod_num == 1:  # E -> E + T
                    t_val = attr_stack.pop()
                    e1_val = attr_stack.pop()
                    e_val = self.newtemp()
                    self.emit(f"{e_val} := {e1_val} + {t_val}")
                    attr_stack.append(e_val)
                
                elif prod_num == 11:  # E -> E - T
                    t_val = attr_stack.pop()
                    e1_val = attr_stack.pop()
                    e_val = self.newtemp()
                    self.emit(f"{e_val} := {e1_val} - {t_val}")
                    attr_stack.append(e_val)
                
                elif prod_num == 2:  # E -> T
                    pass
                
                elif prod_num == 3:  # T -> T * F
                    f_val = attr_stack.pop()
                    t1_val = attr_stack.pop()
                    t_val = self.newtemp()
                    self.emit(f"{t_val} := {t1_val} * {f_val}")
                    attr_stack.append(t_val)
                
                elif prod_num == 31:  # T -> T / F
                    f_val = attr_stack.pop()
                    t1_val = attr_stack.pop()
                    t_val = self.newtemp()
                    self.emit(f"{t_val} := {t1_val} / {f_val}")
                    attr_stack.append(t_val)
                
                elif prod_num == 4:  # T -> F
                    pass
                
                elif prod_num == 5:  # F -> (E)
                    # Remove '(' ')'
                    e_val = attr_stack.pop()
                    attr_stack.append(e_val)  # F.p = E.p
                
                elif prod_num == 6:  # F -> a
                    pass
                
                elif prod_num == 51:  # F -> -(E)
                    e_val = attr_stack.pop()
                    f_val = self.newtemp()
                    self.emit(f"{f_val} := uminus {e_val}")
                    attr_stack.append(f_val)
                
                goto_state = int(self.parsing_table[stack[-1]][left])
                stack.append(goto_state)
            
            step += 1
            if step > 100:
                return None

def main():
    
    translator = LR1Translator()
    
    translator.compute_first_sets()
    translator.build_canonical_collection()
    translator.build_parsing_table()
    
    test_inputs = [
        "a+a*a", 
        "(a+a)*a", 
        "a*a+a", 
        "a",
        "a+a",
        "a*a*a",
        "(a)", 
        "a+a-a",
        "-(a+a)"
    ]
    
    for test_input in test_inputs:
        print(f"\nInput: {test_input}")
        
        code = translator.translate_input(test_input)
        
        if code:
            if len(code) > 0:
                print("Cod Intermediar:")
                for i, line in enumerate(code, 1):
                    print(f"  {i}. {line}")
            else:
                print("  (no intermediate code - direct value)")
        else:
            print("  ERROR: Translation failed")
        print("-" * 80)

if __name__ == "__main__":
    main()