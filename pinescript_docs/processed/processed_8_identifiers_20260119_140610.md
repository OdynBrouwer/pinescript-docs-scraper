## 8_identifiers_20260119_140610
# 8_identifiers

Source: https://www.tradingview.com/pine-script-docs/language/identifiers

 
    * Pine Script® primer
              * Language
                                                                  * Visuals
                                              * Concepts
                                                      * Writing scripts
                      * FAQ
                                                          * Migration guides
                          

 
Clear
Search results
 
![](https://www.tradingview.com/pine-script-docs/language/identifiers/)
    * Pine Script® primer
              * Language
                                                                  * Visuals
                                              * Concepts
                                                      * Writing scripts
                      * FAQ
                                                          * Migration guides
                          

 User Manual  / Language / Identifiers
#  Identifiers
Identifiers are names used for user-defined variables and functions:
  * They must begin with an uppercase (`A-Z`) or lowercase (`a-z`) letter, or an underscore (`_`).
  * The next characters can be letters, underscores or digits (`0-9`).
  * They are case-sensitive.


Here are some examples:
Pine Script®
Copied
`myVar  
_myVar  
my123Var  
functionName  
MAX_LEN  
max_len  
maxLen  
3barsDown  // NOT VALID!  
`
The Pine Script® Style Guide recommends using uppercase SNAKE_CASE for constants, and camelCase for other identifiers:
Pine Script®
Copied
`GREEN_COLOR = #4CAF50  
MAX_LOOKBACK = 100  
int fastLength = 7  
// Returns 1 if the argument is `true`, 0 if it is `false` or `na`.  
zeroOne(boolValue) => boolValue ? 1 : 0  
`
 Previous   Next Variable declarations