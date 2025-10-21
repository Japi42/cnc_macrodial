Case for the cnc_macrodial.

Print is in two parts - the main body, and then a cover for the Adafruit macropad board.

The body should be printed flat on the bed with no supports.

The top (board cover) should be printed flat on the bed with supports.

Parts:
-[Adafruit MACROPAD Bare Bones](https://www.adafruit.com/product/5100)
-[CNC Rotary Encoder - 60mm](https://www.adafruit.com/product/5735)  
-[Stemma QT cable 150mm](https://www.adafruit.com/product/4209)
-[USB cable](https://www.amazon.com/dp/B0CFZRYFZB), right angle if you want a bottom exit for the cable
-[12 Cherry MX switches](https://www.adafruit.com/product/6022), low profile prefered.
-[12 MX switch key caps]()
-[Rotary encoder cap - slim](https://www.adafruit.com/product/5093)
-4x M3 socket cap screws 

Tools:
-Small hex driver
-M3 allen wrench
-Wire stripper

Assembly:
-Cut off the non-JST end of the Stemma cable, strip off the cover about 1/2" on each wire
-Screw the bare wires to the CNC Rotary Encoder
-Ensure the black encoder gasket is still on the encoder
-Feed the wire through the hole between the CNC encoder recess and the board recess
-Attach the CNC encoder using the supplied nuts
-Remove the nut on the MACROPAD rotary encoder
-Place the 3D printed enclosure top on the MACROPAD board
-Screw on the nut on the MACROPAD rotary encoder
-Attach the rotary encoder cap
-Mount the MX switches and key caps
-Attach the Stemma QT cable to the side of the MACROPAD
-Place the assembled board into the enclosure, starting with the left side to allow the STEMMA QA cable to clear the edge of the case
-Fasten the board with the 4 M3 socket cap screws.
-Plug the USB cable into the top
-If you want the USB cable coming out the bottom of the enclosure, push it into the channel.
-Flash the MACROPAD with the Circuitpython firmware
-Reboot the MACROPAD
-Copy the contents of the cnc_macropad folder onto the CIRCUITPY share (you want the code.py and boot.py to be copied into the root of CIRCUITPY)

