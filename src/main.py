
# class Frame():
#     def __init__(self, variables) -> None:
#         if list == type(variables):
#             self.frame = variables
#         else:
#             self.frame = []
            
# class LocalFrame(Frame):
#     def __init__(self, variables) -> None:
#         super().__init__(variables)


ALL_VARIABLES = {0: [], 1: [], 2: []}
CURR_LEVEL = 0

def local_frame():
    local_variables = ALL_VARIABLES.get(CURR_LEVEL)
    def go_deeper():
        nonlocal local_variables
        CURR_LEVEL = CURR_LEVEL + 1
        
        
def exit_frame():
      
    


if __name__ == "__main__":
    # f(a, b)
    # inside f
    # c = neco
    # g(b, c)
    # inside g
    # print(a) -> error
    
    first = 1
    LOCAL_VARIABLES.append(first)
    local_frame()
    # _______________________
    a = "a"
    LOCAL_VARIABLES.append(a)
    local_frame()
    # _______________________
    b = "b"
    LOCAL_VARIABLES.append(b)
    
    try:
        print(a)
    except AttributeError():
        print("mimo ramec")
        
    exit_frame()
    exit_frame()
    
    
    
    pass