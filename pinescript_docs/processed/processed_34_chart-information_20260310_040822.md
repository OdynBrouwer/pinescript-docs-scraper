## Introduction
The way scripts can obtain information about the chart and symbol they are currently running on is through a subset of Pine Script®‘s built-in variables. The ones we cover here allow scripts to access information relating to:
  * The chart’s prices and volume
  * The chart’s symbol
  * The chart’s timeframe
  * The session (or time period) the symbol trades on

## Prices and volume
The built-in variables for OHLCV values are:
          

Other values are available through:
      

On historical bars, the values of the above variables do not vary during the bar because only OHLCV information is available on them. When running on historical bars, scripts execute on the bar’s close, when all the bar’s information is known and cannot change during the script’s execution on the bar.
Realtime bars are another story altogether. When indicators (or strategies using `calc_on_every_tick = true`) run in realtime, the values of the above variables (except open) will vary between successive iterations of the script on the realtime bar, because they represent their **current** value at one point in time during the progress of the realtime bar. This may lead to one form of repainting. See the page on Pine Script’s execution model for more details.
The [[]] history-referencing operator can be used to refer to past values of the built-in variables, e.g., `close[1]` refers to the value of close on the previous bar, relative to the particular bar the script is executing on.

## Symbol information
Built-in variables in the `syminfo` namespace provide scripts with information on the symbol of the chart the script is running on. This information changes every time a script user changes the chart’s symbol. The script then re-executes on all the chart’s bars using the new values of the built-in variables:
                            

This script displays these built-in variables and their values for the current symbol in a table on the chart:
!image
Pine Script®
Copied
`//@version=6  
indicator("`syminfo.*` built-ins demo", overlay = true)  
  
//@variable The `syminfo.*` built-ins, displayed in the left column of the table.  
string txtLeft =  
  "syminfo.basecurrency: "  + "\n" +  
  "syminfo.currency: "      + "\n" +  
  "syminfo.description: "   + "\n" +  
  "syminfo.main_tickerid: " + "\n" +  
  "syminfo.mincontract: "   + "\n" +  
  "syminfo.mintick: "       + "\n" +  
  "syminfo.pointvalue: "    + "\n" +  
  "syminfo.prefix: "        + "\n" +  
  "syminfo.root: "          + "\n" +  
  "syminfo.session: "       + "\n" +  
  "syminfo.ticker: "        + "\n" +  
  "syminfo.tickerid: "      + "\n" +  
  "syminfo.timezone: "      + "\n" +  
  "syminfo.type: "  
  
//@variable The values of the `syminfo.*` built-ins, displayed in the right column of the table.  
string txtRight =  
  syminfo.basecurrency              + "\n" +  
  syminfo.currency                  + "\n" +  
  syminfo.description               + "\n" +  
  syminfo.main_tickerid             + "\n" +  
  str.tostring(syminfo.mincontract) + "\n" +  
  str.tostring(syminfo.mintick)     + "\n" +  
  str.tostring(syminfo.pointvalue)  + "\n" +  
  syminfo.prefix                    + "\n" +  
  syminfo.root                      + "\n" +  
  syminfo.session                   + "\n" +  
  syminfo.ticker                    + "\n" +  
  syminfo.tickerid                  + "\n" +  
  syminfo.timezone                  + "\n" +  
  syminfo.type  
  
if barstate.islast  
    var table t = table.new(position.middle_right, 2, 1)  
    table.cell(t, 0, 0, txtLeft, bgcolor = color.yellow, text_halign = text.align_right)  
    table.cell(t, 1, 0, txtRight, bgcolor = color.yellow, text_halign = text.align_left)  
`

## Chart timeframe
A script can obtain information on the type of timeframe used on the chart using these built-ins, which all return a “simple bool” result:
              

Additional built-ins return more specific timeframe information:
      

See the page on Timeframes for more information.

## Session information
Session information is available in different forms:
  * The syminfo.session built-in variable returns a value that is either session.regular or session.extended. It reflects the session setting on the chart for that symbol. If the “Chart settings/Symbol/Session” field is set to “Extended”, it will only return “extended” if the symbol and the user’s feed allow for extended sessions. It is used when a session type is expected, for example as the argument for the `session` parameter in ticker.new().
  

 Previous   Next Inputs