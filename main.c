#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#include "gramatica_defines.h"
/************************************
        Define Macros
*************************************/
#ifndef GRAMATICA_DEFINES_INCLUDED
    #define GRAMATICA_DEFINES
    #define ROWS 12
    #define COLUMNS 10
    #define MAX_SYMBOL_LENGTH 4
    #define RANDOM_CHARS 13
    #define PRODUCTIONS 8
#endif // GRAMATICA_DEFINES
#ifdef __GNUC__ //We don't have _WIN32 , only __GNUC__
    #define _WIN32
#endif
/************************************
    Assign fixed size vars in data segment
*************************************/
/************************************
        Define Enums
*************************************/
typedef enum {
    HANDLE_SUCCESS          = 0x00000000, // Standard OS-style success code
    HANDLE_MALLOC_FAIL      = 0xAAAAAAFF,
    HANDLE_FILE_FAIL        = 0xAAAAAACC,
    HANDLE_FILE_INVALID_ATTR= 0xAAAAAADD,
    HANDLE_GENERAL_ERROR    = 0xC0000005
} handleError_t;
/************************************
        Define Structs
*************************************/
typedef struct {
    char ***symbols; //append it to the table
    unsigned char init_symbol, termen, factor;
    unsigned int stack_length; //init symbols
    char **stack,*left,**right;
    char *randoms; //( ) * / + etc.
}grammar_elements;
/************************************
        Define Global Variables
*************************************/
static FILE* gramatica_productie = NULL; //visible only in .c
static FILE* tabel_actiuni = NULL;
DWORD file_attributes_productie, file_tabel;
grammar_elements *ob_grammar = NULL;
char **initial_message = NULL;

/************************************
        Define Global functions
*************************************/
unsigned long mapToSysError(handleError_t err){
    //GNUC is defined and we customly define _WIN32
    #ifdef _WIN32
    #pragma message("_WIN32 is defined")
    // Windows Error Mapping : return Win32 error codes universally recognized by Windows Sys Calls
    switch(err){
        case HANDLE_SUCCESS:    return ERROR_SUCCESS;
        case HANDLE_MALLOC_FAIL:return ERROR_NOT_ENOUGH_MEMORY;
        case HANDLE_FILE_FAIL  :return ERROR_FILE_NOT_FOUND;
        case HANDLE_FILE_INVALID_ATTR: return ERROR_INVALID_PARAMETER;
        case HANDLE_GENERAL_ERROR: return ERROR_GEN_FAILURE;
        default : return ERROR_GEN_FAILURE;
    }
    #endif // _WIN32
}
//The function static has internal linkage
static void _init_files(FILE** _file_gramatica_prod, FILE** _file_tabel_actiuni){
    *_file_gramatica_prod = fopen("gramatica_productie.txt","r");
    *_file_tabel_actiuni = fopen("tabel_fin.txt","w");
}
static void _initialize_members(grammar_elements *param_ob_gramatica){
    param_ob_gramatica->init_symbol = fgetc(gramatica_productie); fgetc(gramatica_productie);
    param_ob_gramatica->termen = fgetc(gramatica_productie); fgetc(gramatica_productie);
    param_ob_gramatica->factor = fgetc(gramatica_productie); fgetc(gramatica_productie);
    param_ob_gramatica->randoms = malloc(RANDOM_CHARS*sizeof(char));
    param_ob_gramatica->left = malloc(PRODUCTIONS*sizeof(char));
    param_ob_gramatica->right = malloc(PRODUCTIONS*sizeof(char*));
    for(unsigned levels = 0; levels < PRODUCTIONS; levels++)
        param_ob_gramatica->right[levels] = malloc(5*sizeof(char));
    param_ob_gramatica->symbols = malloc(ROWS * sizeof(char**));
    for(unsigned row = 0 ; row < ROWS; row++){
        param_ob_gramatica->symbols[row] = malloc(COLUMNS*sizeof(char*));
        for(unsigned element = 0; element < COLUMNS; element++)
            param_ob_gramatica->symbols[row][element] = malloc(MAX_SYMBOL_LENGTH*sizeof(char));
    }
    param_ob_gramatica->stack = malloc(50*sizeof(char*)); //arbitrary
    for(unsigned levels = 0; levels < 50; levels++)
        param_ob_gramatica->stack[levels] = malloc(3*sizeof(char));
}
static void _initialize_message(void){
    initial_message = malloc(10*sizeof(char*)); //arbitrary
    for(unsigned i=0; i<10;i++)
        initial_message[i] = malloc(3*sizeof(char));
    strcpy(initial_message[0],"id"); strcpy(initial_message[1],"+");
    strcpy(initial_message[2],"id"); strcpy(initial_message[3],"*");
    strcpy(initial_message[4],"id"); strcpy(initial_message[5],"$");
    printf("\n  Initial message : ");
    for(unsigned i=0;i<6;i++)
        printf("%s",initial_message[i]);

}
static void _initialize_stack(grammar_elements *param_ob_gramatica){
    if(!param_ob_gramatica->stack) { return; }
    param_ob_gramatica->stack_length = 0;
    param_ob_gramatica->stack[param_ob_gramatica->stack_length] = "0";
    printf("\n  Initial Stack: %s",param_ob_gramatica->stack[param_ob_gramatica->stack_length]);
}
static void _read_production(grammar_elements *param_ob_gramatica) {
    for(unsigned rnd_chars = 0;rnd_chars < RANDOM_CHARS && param_ob_gramatica->randoms[rnd_chars]!= 0x0A; rnd_chars++)
        param_ob_gramatica->randoms[rnd_chars] = fgetc(gramatica_productie);
    fgetc(gramatica_productie); //Get the ENTER
    param_ob_gramatica->init_symbol = fgetc(gramatica_productie);
    fgetc(gramatica_productie); //Get the ENTER again
    printf("\n  Init Symbol %c",param_ob_gramatica->init_symbol);
    printf("\n  ");
    for(unsigned i=0;i<RANDOM_CHARS;i++)
        printf("%c",param_ob_gramatica->randoms[i]);
    printf("\n  %c",param_ob_gramatica->init_symbol);
    char current_char = NULL, *temp_right = NULL;
    unsigned left_index=0, right_index=0, temp_right_index=0;
    while( (current_char = fgetc(gramatica_productie)) != EOF){
        temp_right_index = 0;
        temp_right = malloc(MAX_SYMBOL_LENGTH*sizeof(char));
        //We have to get the first char then simulate space
        param_ob_gramatica->left[left_index++] = current_char; fgetc(gramatica_productie);
        //Go till the end of the row , get the char and verify if it's not ENTER keybind
        while((current_char = fgetc(gramatica_productie)) != EOF && current_char != 0x0A) { temp_right[temp_right_index++] = current_char; }
        temp_right[temp_right_index] = '\0'; //Null terminator for char*
        strcpy(param_ob_gramatica->right[right_index++],temp_right);
        //TEST printf("\n%s",param_ob_gramatica->right[right_index]); right_index++;
        free(temp_right);
    }
    for(unsigned i=0; i< PRODUCTIONS-1; i++){
        printf("\n  %c %s",param_ob_gramatica->left[i],param_ob_gramatica->right[i]);
    }
}
static void _init_hardcoded_symbols(grammar_elements *param_ob_gramatica){
    // Initialize ALL cells with empty strings first
    for(unsigned row = 0; row < ROWS; row++){
        for(unsigned column = 0; column < COLUMNS; column++){
            strcpy(param_ob_gramatica->symbols[row][column], ""); // Use strcpy to set empty string
        }
    }

    // Now set only the header row (row 0)
    strcpy(param_ob_gramatica->symbols[0][0], "id");
    strcpy(param_ob_gramatica->symbols[0][1], "+");
    strcpy(param_ob_gramatica->symbols[0][2], "*");
    strcpy(param_ob_gramatica->symbols[0][3], "(");
    strcpy(param_ob_gramatica->symbols[0][4], ")");
    strcpy(param_ob_gramatica->symbols[0][5], "$");
    strcpy(param_ob_gramatica->symbols[0][6], "E");
    strcpy(param_ob_gramatica->symbols[0][7], "T");
    strcpy(param_ob_gramatica->symbols[0][8], "F");
    // Column 9 remains empty

    printf("\n  ====== SYMBOLS TABLE INITIALLY======\n");
    for(unsigned row = 0; row < ROWS; row++){
        printf("Row %d: ", row);
        for(unsigned column = 0; column < COLUMNS -1; column++){
            if(strlen(param_ob_gramatica->symbols[row][column]) > 0) {
                printf("[%s] ", param_ob_gramatica->symbols[row][column]);
            } else {
                printf("[ ] "); // Show empty cells as blank
            }
        }
        printf("\n");
    }
}

int main()
{
    /******************************************
        MALLOC/FREE MAIN FUNC VARS IN USE
    ******************************************/
    printf("=======LR 1 PARSER : Declare gramamar elements==========");
    ob_grammar = malloc(sizeof(grammar_elements));
    unsigned long error_code = malloc(sizeof(unsigned long)); //DWORD ASM

    /************************************************
        ALLOCATE MEM AND HANDLE ERRORS
    *************************************************/
    //Double Word declaration of err
    if(ob_grammar == NULL){ goto MEM_FAIL_HANDLE; }
    _init_files(&gramatica_productie, &tabel_actiuni);
    if(!gramatica_productie || !tabel_actiuni) { goto MEM_FAIL_HANDLE; }
    else {
            printf("\n ----- FILES DECLARED ----");
            printf("\n      - Production File of number %d",PRODUCTIONS);
            printf("\n      - Tabel File to Append");
    }
    _initialize_members(ob_grammar);
    file_attributes_productie = GetFileAttributes("gramatica_productie.txt");
    file_tabel = GetFileAttributes("tabel_actiuni.txt");
    //Dont activate this if, something is wrong
    if(file_attributes_productie == INVALID_FILE_ATTRIBUTES || file_tabel == INVALID_FILE_ATTRIBUTES)
        //goto FILE_INVALID_ATTR;
    if(!ob_grammar) { goto FILE_FAIL_HANDLE; }
    else { printf("\n ----- GRAMMAR MEMBERS INITIALIZED ----"); }


    _read_production(ob_grammar);
    _init_hardcoded_symbols(ob_grammar);
    _initialize_message();
    if(!initial_message) { goto MEM_FAIL_HANDLE; }
    _initialize_stack(ob_grammar);
    free(ob_grammar);
    free(error_code);
    return HANDLE_SUCCESS;

    /*  ERROR_FILE_NOT_FOUND = 2 file does not exist
        ERROR_INVALID_PARAMETER = 87 bad parameter
        ERROR_INVALID_HANDLE = 6 invalid handle
        ERROR_INVALID_ACCESS = 12 access denied
        ERROR_INVALID_DATA = 13 data is invalid
        ERROR_INVALID_NAME = 123 bad file name
        ERROR_INVALID_DRIVE = 15 drive letter invalid
        ERROR_INVALID_FUNCTION = 1  function not supported */
    MEM_FAIL_HANDLE:
        error_code = mapToSysError(HANDLE_MALLOC_FAIL);
        SetLastError(error_code);
        printf("\nMemory allocation failed. Windows error code: %lu\n", GetLastError()); // 8
        free(ob_grammar);
        free(error_code);
    FILE_FAIL_HANDLE:
        error_code = mapToSysError(HANDLE_FILE_FAIL);
        SetLastError(error_code);
        printf("\nFile Opening failed. Windows error code: %lu\n", GetLastError()); // 8
        free(ob_grammar);
        free(error_code);
    FILE_INVALID_ATTR:
        error_code = mapToSysError(HANDLE_FILE_INVALID_ATTR);
        SetLastError(error_code);
        printf("\nFile Attributes are wrong. Windows error code: %lu\n", GetLastError()); // 8
        free(ob_grammar);
        free(error_code);
}
