# SPDX-FileCopyrightText: 2025 Jason Pimble
#
# SPDX-License-Identifier: Unlicense
"""
Simple multi-page control for CNC and Lasers

Hardware is built around an Adafruit Macropad

Each page has different macros assigned to the buttons.

Pages needed:
-Dial jogging
-Arrow jogging
-Job Control
-Rapid movement (Goto)
-Probe control
-View control
-Lightburn jog

TODO:
-Better page switching
-Burn-in protection
-Button handling - long press/short press
-Display primitives

"""

from rainbowio import colorwheel

from adafruit_macropad import MacroPad
import rotaryio
import usb_hid
import board
import asyncio
import time
import displayio
import terminalio
import gc
from adafruit_display_text import bitmap_label as label
from adafruit_displayio_layout.layouts.grid_layout import GridLayout

import adafruit_radial_controller

class LedMode:
    OFF = 0
    ON = 1
    BLINK = 2
    PULSE = 3

class KeyMode:
    NONE = 0
    MOMENT = 1
    LONG_MOMENT = 2
    PRESS = 3

class LedState:
    def __init__(self, on_color=(255,255,255), mode=LedMode.OFF, interval=0.1):
        self.on_color = on_color
        self.off_color = (0, 0, 0)
        self.mode = mode
        self.interval = interval
        self.event = asyncio.Event()

    def reset(self):
        self.mode = LedMode.OFF

    def set_on_color(self, on_color):
        self.on_color = on_color
        self.event.set()

    def set_off_color(self, off_color):
        self.off_color = off_color
        self.event.set()

    def set_mode(self, mode):
        self.mode = mode
        self.event.set()
        
class KeyState:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.pressed = False
        self.press_time = None
        self.press_duration = 0
        self.release_time = None

class KeySettings:
    def __init__(self, name="", on_color=(255,255,255), off_color=(0,0,0), mode=KeyMode.NONE):
        self.name = name
        self.on_color = on_color
        self.off_color = off_color
        self.mode = mode
        self.press_callback = None
        self.release_callback = None
        self.hold_callback = None
        self.long_moment_time = 2
        
class OverallState:
    def __init__(self):
        self.last_interaction = None
        self.page_stack = list()
        self.selection_page = None
        self.current_page = None
        self.previous_page = None
        self.led_states = list()
        self.key_states = list()

        self.sleep_page = None
        self.wake_to_page = None
        self.sleep_time = 60 * 15

        for i in range(0,12):
            self.led_states.append(LedState())
            self.key_states.append(KeyState())

    def reset(self):
        for i in range(0,12):
            self.led_states[i].reset()
            self.key_states[i].reset()
            
    def add_page(self, page):
        self.page_stack.append(page)
        if self.current_page is None:
            self.current_page = page
            self.current_page.activate()
            
class DisplayPage:
    def __init__(self, state, title=None):
        self.state = state
        self.title = title
        self.key_settings = list()
        self.main_group = None
        for i in range(0, 12):
            self.key_settings.append(KeySettings(name=""))
    
    def handle_key_event(self, key_event):
        if key_event.pressed and self.key_settings[key_event.key_number].mode != KeyMode.NONE:
            self.state.led_states[key_event.key_number].set_mode(LedMode.ON)
            if self.key_settings[key_event.key_number].press_callback:
                self.key_settings[key_event.key_number].press_callback()
        if not key_event.pressed:
            if self.key_settings[key_event.key_number].release_callback:
                self.key_settings[key_event.key_number].release_callback()
            self.state.led_states[key_event.key_number].set_mode(LedMode.OFF)
            
    def handle_jog_event(self, change_rel, absolute_value):
        pass

    def handle_encoder_press(self, pressed):

        if pressed and self.state.selection_page:
            self.state.current_page.deactivate()
            self.state.previous_page = self.state.current_page
            self.state.current_page = self.state.selection_page
            self.state.current_page.activate()
    
    def handle_encoder_event(self, change_rel, absolute_value):
        pass

    def activate(self):
        for i in range(0,12):
            self.state.led_states[i].set_on_color(self.key_settings[i].on_color)
            self.state.led_states[i].set_off_color(self.key_settings[i].off_color)
            self.state.led_states[i].set_mode(LedMode.OFF)

        self.main_group = displayio.Group()
        macropad.display.root_group = self.main_group
        if self.title is not None:
            title_label = label.Label(
                x=64,
                y=4,
                font=terminalio.FONT,
                color=0x0,
                text="        "+self.title+"        ",
                background_color=0xFFFFFF,
                anchor_point=(0.5,0.5),
                anchored_position=(64,4)
            )
            self.main_group.append(title_label)
        
    def deactivate(self):
        self.main_group = None
        gc.collect()
        print("Free memory at code point 1: {} bytes".format(gc.mem_free()) )

"""
The page used to switch between other pages
"""

class SelectionPage(DisplayPage):

    def __init__(self, state, title=None):
        super().__init__(state, title=title)
        self.selected_page = None
    
    def handle_encoder_press(self, pressed):
        if pressed and self.state.selection_page:
            self.state.current_page.deactivate()
            self.state.current_page = self.selected_page
            self.state.current_page.activate()

    def activate(self):
        super().activate()
        self.selected_page = self.state.previous_page

        self.selection = label.Label(
            x=64,
            y=20,
            font=terminalio.FONT,
            color=0xffffff,
            scale=2,
            text=self.selected_page.title,
            background_color=0x000000,
            anchor_point=(0.5,0.5),
            anchored_position=(64,32),
        )
        
        self.main_group.append(self.selection)
        
    def handle_encoder_event(self, change_rel, absolute_value):
        index = self.state.page_stack.index(self.selected_page)

        if change_rel < 0:
            index -= 1
            if index < 0:
                index = len(self.state.page_stack)-1
                
        if change_rel > 0:
            index += 1
            if index >= len(self.state.page_stack):
                index = 0

        self.selected_page = self.state.page_stack[index]
        self.selection.text = self.selected_page.title

"""
The page used when going to sleep
"""

class SleepPage(DisplayPage):

    def __init__(self, state, title=None):
        super().__init__(state, title=title)
    
    def activate(self):
        super().activate()

    def wake(self):
        self.state.current_page.deactivate()
        self.state.current_page = self.state.wake_to_page
        self.state.current_page.activate()
        
    def handle_encoder_press(self, pressed):
        if pressed:
            self.wake()
        
    def handle_encoder_event(self, change_rel, absolute_value):
        self.wake()
        
"""
A basic page that handles simple button presses

"""
class SimpleButtonPage(DisplayPage):

    def activate(self):
        super().activate()

        layout = GridLayout(x=0, y=10, width=128, height=54, grid_size=(3, 4), cell_padding=1, divider_lines=True, cell_anchor_point=(0.5,0.5))
        labels = []
        for j in range(12):
            labels.append(label.Label(terminalio.FONT, text=self.key_settings[j].name))
        
        for index in range(12):
            x = index % 3
            y = index // 3
            layout.add_content(labels[index], grid_position=(x, y), cell_size=(1, 1))
        
        self.main_group.append(layout)
    
"""
A page for jog dialing, in gSender

"""
class JogDialPage(DisplayPage):

    def __init__(self, state, title=None):
        super().__init__(state, title=title)
        self.selected_axis = None
    
    def activate(self):
        super().activate()

        self.selected_axis = None
        
        layout = GridLayout(x=0, y=10, width=128, height=54, grid_size=(3, 4), cell_padding=1, divider_lines=True, cell_anchor_point=(0.5,0.5))
        labels = []
        for j in range(12):
            labels.append(label.Label(terminalio.FONT, text=self.key_settings[j].name))
        
        for index in range(12):
            x = index % 3
            y = index // 3
            layout.add_content(labels[index], grid_position=(x, y), cell_size=(1, 1))
        
        self.main_group.append(layout)
    
    def handle_jog_event(self, change_rel, absolute_value):

        for i in range(0, abs(change_rel)):
            if change_rel < 0 and self.selected_axis == 0:
                macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.LEFT_ARROW)
            elif change_rel > 0 and self.selected_axis == 0:
                macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.RIGHT_ARROW)
            elif change_rel < 0 and self.selected_axis == 1:
                macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.DOWN_ARROW)
            elif change_rel > 0 and self.selected_axis == 1:
                macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.UP_ARROW)
            elif change_rel < 0 and self.selected_axis == 2:
                macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.PAGE_DOWN)
            elif change_rel > 0 and self.selected_axis == 2:
                macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.PAGE_UP)

    def select_axis(self, axis):

        # If selecting the current axis, turn it off
        
        if axis == self.selected_axis:
            self.selected_axis = None
        else:
            self.selected_axis = axis

        # Adjust the LED states

        if self.selected_axis == 0:
            self.state.led_states[9].set_off_color( (255, 0, 20))
        else:
            self.state.led_states[9].set_off_color( (0, 32, 32))

        if self.selected_axis == 1:
            self.state.led_states[10].set_off_color( (255, 0, 20))
        else:
            self.state.led_states[10].set_off_color( (0, 32, 32))

        if self.selected_axis == 2:
            self.state.led_states[11].set_off_color( (255, 0, 20))
        else:
            self.state.led_states[11].set_off_color( (0, 32, 32))
            
        
# Button LED Control

async def led_task(key_number, state):
    last_update = time.monotonic_ns()
    
    while True:
        this_update = time.monotonic_ns()

        if state.mode == LedMode.OFF:
            macropad.pixels[key_number] = state.off_color
        elif state.mode == LedMode.ON:
            macropad.pixels[key_number] = state.on_color
        elif state.mode == LedMode.BLINK:
            if int(this_update / (state.interval * 1000000000)) % 2:
                macropad.pixels[key_number] = state.on_color
            else:
                macropad.pixels[key_number] = state.off_color

        last_update = this_update
        if state.mode == LedMode.BLINK:
            await asyncio.sleep(0.001)
        else:
            await state.event.wait()
            state.event.clear()

# Main event loop
# Handles page changes via the rotary encoder
# Passes key/jog dial events to the current page

async def event_loop_task(state):
    macropad.encoder_switch_debounced.update()

    last_jog_pos = jog_enc.position
    last_encoder_pos = macropad.encoder
    encoder_held = False

    state.last_interaction = time.monotonic_ns()
    
    while True:

        current_time = time.monotonic_ns()
        
        # Check if we need to change the page based on the rotary encoder being pressed

        macropad.encoder_switch_debounced.update()

        if macropad.encoder_switch_debounced.pressed:
            if not encoder_held:
                state.current_page.handle_encoder_press(True)
                encoder_held = True
                state.last_interaction = current_time
        else:
            state.current_page.handle_encoder_press(False)
            encoder_held = False
        
        # Pass through any key events to the active page
        
        key_event = macropad.keys.events.get()

        if key_event:
            state.current_page.handle_key_event(key_event)
            state.last_interaction = current_time

        # Pass through any long-held key events

        
            
        # Pass through the jog dial events to the active page
            
        cur_jog_pos = jog_enc.position
        if cur_jog_pos != last_jog_pos:
            change_rel = cur_jog_pos - last_jog_pos 
            state.current_page.handle_jog_event(change_rel, cur_jog_pos)
            last_jog_pos = cur_jog_pos
            state.last_interaction = current_time

        # Pass through rotary encoder events to the active page

        cur_encoder_pos = macropad.encoder
        if cur_encoder_pos != last_encoder_pos:
            change_rel = cur_encoder_pos - last_encoder_pos 
            state.current_page.handle_encoder_event(change_rel, cur_encoder_pos)
            last_encoder_pos = cur_encoder_pos
            state.last_interaction = current_time

        if state.current_page != state.sleep_page and (current_time - state.last_interaction) > (state.sleep_time * 1000000000):
            state.current_page.deactivate()
            state.wake_to_page = state.current_page
            state.current_page = state.sleep_page
            state.current_page.activate()
            
        await asyncio.sleep(0)
        
async def main():
    state = OverallState()

# Set up the sleep page

    sleep_page = SleepPage(state, title=None)
    state.sleep_page = sleep_page
    
# Set up the selection page

    selection_page = SelectionPage(state, title="Selection")
    state.selection_page = selection_page
    
    # Set up test page
    
#    test_page = SimpleButtonPage(state, title="Test")
#
#    test_page.key_settings[0] = KeySettings(name="X",on_color=(255,0,20), off_color=(0,0,32), mode=KeyMode.MOMENT)
#    test_page.key_settings[0].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.B)
#
#    test_page.key_settings[1] = KeySettings(name="Y",on_color=(255,0,20), off_color=(0,0,32), mode=KeyMode.MOMENT)
#    test_page.key_settings[1].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.C)
#
#    test_page.key_settings[2] = KeySettings(name="Z",on_color=(255,0,20), off_color=(0,0,32), mode=KeyMode.MOMENT)
#    test_page.key_settings[2].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.D)
#
#    test_page.key_settings[3] = KeySettings(name="GP",on_color=(255,0,20), off_color=(0,0,32), mode=KeyMode.MOMENT)
#    test_page.key_settings[3].press_callback = button_test
#
#    state.add_page(test_page)

    # Set up job control page
    
    job_control_page = SimpleButtonPage(state, title="Job Control")
 
    job_control_page.key_settings[0] = KeySettings(name="Stop",on_color=(255,0,0), off_color=(32,0,0), mode=KeyMode.MOMENT)
    job_control_page.key_settings[0].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.TWO)

    job_control_page.key_settings[1] = KeySettings(name="Pause",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    job_control_page.key_settings[1].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.ONE)

    job_control_page.key_settings[2] = KeySettings(name="Start",on_color=(0,255,0), off_color=(0,32,0), mode=KeyMode.MOMENT)
    job_control_page.key_settings[2].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.GRAVE_ACCENT)
    
    state.add_page(job_control_page)

    # Set up the arrow jog page

    arrow_jog_page = SimpleButtonPage(state, title="Arrow Jog")

    arrow_jog_page.key_settings[3] = KeySettings(name="Precise",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    arrow_jog_page.key_settings[3].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.X)

    arrow_jog_page.key_settings[4] = KeySettings(name="Normal",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    arrow_jog_page.key_settings[4].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.C)

    arrow_jog_page.key_settings[5] = KeySettings(name="Rapid",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    arrow_jog_page.key_settings[5].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.V)

    arrow_jog_page.key_settings[6] = KeySettings(name="Z-",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    arrow_jog_page.key_settings[6].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.PAGE_DOWN)

    arrow_jog_page.key_settings[7] = KeySettings(name="Y+",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    arrow_jog_page.key_settings[7].press_callback = lambda: macropad.keyboard.press(macropad.Keycode.SHIFT, macropad.Keycode.UP_ARROW)
    arrow_jog_page.key_settings[7].release_callback = lambda: macropad.keyboard.release_all()

    arrow_jog_page.key_settings[8] = KeySettings(name="Z+",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    arrow_jog_page.key_settings[8].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.PAGE_UP)

    arrow_jog_page.key_settings[9] = KeySettings(name="X-",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    arrow_jog_page.key_settings[9].press_callback = lambda: macropad.keyboard.press(macropad.Keycode.SHIFT, macropad.Keycode.LEFT_ARROW)
    arrow_jog_page.key_settings[9].release_callback = lambda: macropad.keyboard.release_all()

    arrow_jog_page.key_settings[10] = KeySettings(name="Y-",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    arrow_jog_page.key_settings[10].press_callback = lambda: macropad.keyboard.press(macropad.Keycode.SHIFT, macropad.Keycode.DOWN_ARROW)
    arrow_jog_page.key_settings[10].release_callback = lambda: macropad.keyboard.release_all()

    arrow_jog_page.key_settings[11] = KeySettings(name="X+",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    arrow_jog_page.key_settings[11].press_callback = lambda: macropad.keyboard.press(macropad.Keycode.SHIFT, macropad.Keycode.RIGHT_ARROW)
    arrow_jog_page.key_settings[11].release_callback = lambda: macropad.keyboard.release_all()

    state.add_page(arrow_jog_page)

    # Set up the Jog Dial page

    jog_dial_page = JogDialPage(state, title="Dial Jog")

    jog_dial_page.key_settings[3] = KeySettings(name="Precise",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    jog_dial_page.key_settings[3].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.X)

    jog_dial_page.key_settings[4] = KeySettings(name="Normal",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    jog_dial_page.key_settings[4].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.C)

    jog_dial_page.key_settings[5] = KeySettings(name="Rapid",on_color=(255,0,20), off_color=(32,32,0), mode=KeyMode.MOMENT)
    jog_dial_page.key_settings[5].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.V)
    
    jog_dial_page.key_settings[9] = KeySettings(name="X",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    jog_dial_page.key_settings[9].press_callback = lambda: jog_dial_page.select_axis(0)

    jog_dial_page.key_settings[10] = KeySettings(name="Y",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    jog_dial_page.key_settings[10].press_callback = lambda: jog_dial_page.select_axis(1)

    jog_dial_page.key_settings[11] = KeySettings(name="Z",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    jog_dial_page.key_settings[11].press_callback = lambda: jog_dial_page.select_axis(2)
    
    state.add_page(jog_dial_page)

    # Set up the Probe page

    probe_page = SimpleButtonPage(state, title="Probe")
 
    probe_page.key_settings[0] = KeySettings(name="Stop",on_color=(255,0,0), off_color=(32,0,0), mode=KeyMode.MOMENT)
    probe_page.key_settings[0].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.TWO)

    probe_page.key_settings[1] = KeySettings(name="Pause",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    probe_page.key_settings[1].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.ONE)

    probe_page.key_settings[2] = KeySettings(name="Start",on_color=(0,255,0), off_color=(0,32,0), mode=KeyMode.MOMENT)
    probe_page.key_settings[2].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.GRAVE_ACCENT)

    probe_page.key_settings[4] = KeySettings(name="Open",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    probe_page.key_settings[4].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.A)
    
    probe_page.key_settings[6] = KeySettings(name="Dia -",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    probe_page.key_settings[6].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.A)

    probe_page.key_settings[8] = KeySettings(name="Dia +",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    probe_page.key_settings[8].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.B)
    
    probe_page.key_settings[9] = KeySettings(name="Left",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    probe_page.key_settings[9].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.A)

    probe_page.key_settings[10] = KeySettings(name="Confirm",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    probe_page.key_settings[10].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.A)
    
    probe_page.key_settings[11] = KeySettings(name="Right",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    probe_page.key_settings[11].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.B)
    
    state.add_page(probe_page)

    # Set up rapids control page
    
    rapids_page = SimpleButtonPage(state, title="Rapids")
 
    rapids_page.key_settings[0] = KeySettings(name="Stop",on_color=(255,0,0), off_color=(32,0,0), mode=KeyMode.MOMENT)
    rapids_page.key_settings[0].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.TWO)

    rapids_page.key_settings[1] = KeySettings(name="Pause",on_color=(255,0,20), off_color=(0,32,32), mode=KeyMode.MOMENT)
    rapids_page.key_settings[1].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.ONE)

    rapids_page.key_settings[2] = KeySettings(name="Start",on_color=(0,255,0), off_color=(0,32,0), mode=KeyMode.MOMENT)
    rapids_page.key_settings[2].press_callback = lambda: macropad.keyboard.send(macropad.Keycode.SHIFT, macropad.Keycode.GRAVE_ACCENT)
    
    state.add_page(rapids_page)
    
# Add task handlers for the LEDs
    
    event_task = asyncio.create_task(event_loop_task(state))
    button_tasks = list()
    for i in range(0,12):
        button_tasks.append(asyncio.create_task(led_task(i, state.led_states[i])))

# Kick off everything

    await asyncio.gather(event_task)  

def button_test():
    for i in range(0,100):
        macropad.keyboard.send(macropad.Keycode.A)
        
# Main entry point:

radial_controller = adafruit_radial_controller.RadialController(usb_hid.devices)
macropad = MacroPad()
jog_enc = rotaryio.IncrementalEncoder(board.SCL, board.SDA)
    
asyncio.run(main())
        


