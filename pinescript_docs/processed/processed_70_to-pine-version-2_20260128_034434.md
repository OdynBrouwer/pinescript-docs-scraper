## 70_to-pine-version-2_20260128_034434
# 70_to-pine-version-2

Source: https://www.tradingview.com/pine-script-docs/migration-guides/to-pine-version-2

 
    * Pine Script® primer
              * Language
                                                                  * Visuals
                                              * Concepts
                                                      * Writing scripts
                      * FAQ
                                                          * Migration guides
                          

 
Clear
Search results
 
![](https://www.tradingview.com/pine-script-docs/migration-guides/to-pine-version-2/)
    * Pine Script® primer
              * Language
                                                                  * Visuals
                                              * Concepts
                                                      * Writing scripts
                      * FAQ
                                                          * Migration guides
                          

 User Manual  / Migration guides / To Pine Script® version 2
# To Pine Script® version 2
Pine Script version 2 is fully backwards compatible with version 1. As a result, all v1 scripts can be converted to v2 by adding the `//@version=2` annotation to them.
An example v1 script:
Pine Script®
Copied
`study("Simple Moving Average", shorttitle="SMA")  
src = close  
length = input(10)  
plot(sma(src, length))  
`
The converted v2 script:
Pine Script®
Copied
`//@version=2  
study("Simple Moving Average", shorttitle="SMA")  
src = close  
length = input(10)  
plot(sma(src, length))  
`
 Previous