
/*

  Case for adafuit macropad with CNC dial
  
  Case is printed in two parts
  
  This is for the top part

*/

include <polyround.scad>

// All dimensions are in mm

board_width =  2.35 * 25.4;
board_height = 4.10 * 25.4;
board_cover_thickness = 6.8;
board_overhang = 1; // per side
board_cover_radius = 4;
board_cover_width = board_width + (board_overhang * 2);
board_cover_height = board_height + (board_overhang * 2);
board_cover_spacing = 2.3;

key_cover_thickness = 3.7;
key_top_width = 16.25;
key_top_depth = 10;
key_bottom_width = 14.25;
key_bottom_depth = 2.5;
key_tabs_width = 3.5;
key_tabs_height =  0.6;
key_tabs_depth = 1;

first_key_x_offset = 0;
first_key_y_offset = 2.7; // measured from the bottom
key_x_offset = 19;
key_y_offset = 19;

board_screw_x_spacing = 2.05 * 25.4;
board_screw_y_spacing = 3.20 * 25.4;

rotary_x_offset = (board_cover_width / 2) - 12.5; 
rotary_y_offset = (board_cover_height / 2) - 14.5; 
rotary_shaft_radius = 9 / 2;
rotary_square_width = 13.5;
rotary_square_height = 5.9;

screen_width = 31.2;
screen_height = 16.5;
screen_x_offset = screen_width / 2 + 2 + board_overhang;
screen_y_offset = screen_height / 2 + 2 + board_overhang;

screen_left_xpand = 1.5;
screen_right_xpand = 6.4;
screen_top_xpand = 1.5;
screen_bot_xpand = 14.3;


eps = 0.05;
eps2 = eps*2;

$fn=64;

module key_hole() {
    
    union() {

// larger top hole

      translate([0, 0, key_top_depth/2 + key_bottom_depth]) {
        cube([key_top_width, key_top_width, key_top_depth], center=true);
      }      

// smaller bottom hole

      translate([0, 0, key_bottom_depth/2]) {
        cube([key_bottom_width, key_bottom_width, key_bottom_depth + eps], center=true);
      }      

// cut outs for tabs

      translate([0, 0, key_tabs_depth/2]) {
        cube([key_tabs_width, key_bottom_width + 2*key_tabs_height, key_tabs_depth + eps], center=true);
      }      

    }
    
}

// 4 screw holes for the board
// centered 

module keypad_holes() {

  for(x = [-1 : 1]) {
    for(y = [-1.5 : 1.5]) {
      translate([(x * key_x_offset), 
                 (y * key_y_offset), 
                 0]) {
        key_hole();
      }
    }
  }
}

// hole for mounting the CNC dial

module rotary_hole() {

  union() {

// hole for the rotary shart

    translate([0, 0, 0]) {
      cylinder(60, rotary_shaft_radius, rotary_shaft_radius, center=true);
    }

// hole for the square part

    translate([0, 0, rotary_square_height/2]) {
      rotate([0, 0, 45]) {
        cube([rotary_square_width, rotary_square_width, rotary_square_height + eps], center=true);
      }
    }

  }
  
}

// hole for the screen

module screen_hole() {
    
    union() {
        
        // straight through cut out of the screen
        
        translate([0, 0, 0]) {
            cube([screen_width, screen_height, 20 + eps], center=true);
        }
        
        // the weird trapezoid expansion of the screen, for better viewing angles.
        
        translate([-screen_width/2, -screen_height/2, 0.4]) {
            CubePoints = [
              [  0,                                 0,                                 0 ],  //0
              [ screen_width,                       0,                                 0 ],  //1
              [ screen_width,                       screen_height,                     0 ],  //2
              [  0,                                 screen_height,                     0 ],  //3
              [  -screen_left_xpand,               -screen_bot_xpand,                  6.6 ],  //4
              [ screen_width + screen_right_xpand, -screen_bot_xpand,                  6.6 ],  //5
              [ screen_width + screen_right_xpand,  screen_height + screen_top_xpand,  6.6 ],  //6
              [  -screen_left_xpand,                screen_height + screen_top_xpand,  6.6 ]]; //7
              
            CubeFaces = [
              [0,1,2,3],  // bottom
              [4,5,1,0],  // front
              [7,6,5,4],  // top
              [5,6,2,1],  // right
              [6,7,3,2],  // back
              [7,4,0,3]]; // left
              
            polyhedron( CubePoints, CubeFaces );
        }
        
    }
    
}

// the main cover

module board_cover() {

    difference() {
  
    // main slab
    
        radiiPoints=[[-board_cover_width/2, -board_cover_height/2, board_cover_radius],
                    [ board_cover_width/2, -board_cover_height/2, board_cover_radius],
                    [ board_cover_width/2,  board_cover_height/2, board_cover_radius],
                    [-board_cover_width/2,  board_cover_height/2, board_cover_radius],
                    ];
    
        polyRoundExtrude(radiiPoints, board_cover_thickness, 0, 0, fn=16);
    
    // lower the section for the keys
    
        translate([0, -15, 3 + 10/2]) {
            cube([board_cover_width + eps, 4 * key_y_offset + 10, 10 + eps], center=true);
        }

    }
}

union() {

  difference() {    

// start with the chunk for the board cover

    board_cover();
     
// holes for all the keys

    translate([0, -(board_cover_height - (4 * key_y_offset))/2 + first_key_y_offset , 0]) {
      keypad_holes();
    }
    
// hole for the screen

    translate([-board_cover_width/2 + screen_x_offset, board_cover_height/2 - screen_y_offset, 0]) {
      screen_hole();
    }      

// hole for the rotary control

    translate([rotary_x_offset, rotary_y_offset, 0]) {
      rotary_hole();
    }
   
  }
}

