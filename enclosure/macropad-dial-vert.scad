
/*

  Case for adafuit macropad with CNC dial
  
  Case is printed in two parts

*/

include <polyround.scad>

// All dimensions are in mm

bottom_thickness = 3 + 3;

board_width =  2.35 * 25.4;
board_height = 4.10 * 25.4;
board_thickness = 3;
board_depth = 30 - bottom_thickness;
board_edge_spacing = 0.5;

board_cover_thickness = 6.8+20;
board_overhang = 1; // per side
board_cover_radius = 4;
board_cover_width = board_width + (board_overhang * 2) + board_edge_spacing * 2;
board_cover_height = board_height + (board_overhang * 2) + board_edge_spacing * 2;
board_cover_spacing = 2.3;

board_screw_x_spacing = 2.05 * 25.4;
board_screw_y_spacing = 3.20 * 25.4;

board_screw_x_offset = ((board_width - board_screw_x_spacing) / 2);
board_screw_y_offset_top    = board_screw_x_offset; 
board_screw_y_offset_bottom = (board_height - board_screw_y_spacing - board_screw_y_offset_top); 

cnc_dial_hole_radius = 61 / 2;
cnc_dial_hookup_radius = 43 / 2;
cnc_dial_screw_offset = 51 / 2;
cnc_dial_nut_radius = 12 / 2;
cnc_dial_screw_radius = 3.5 / 2;

board_screw_radius = 3.1 / 2; 
board_screw_depth = 10;

top_padding = 3.4;
side_padding = 9;

main_width =  board_width + (side_padding * 2);
main_height = board_height + (top_padding * 2);
main_depth = 23;

cnc_dial_padding = 15;
cnc_dial_width = main_width;
cnc_dial_height = cnc_dial_hole_radius * 2 + cnc_dial_padding;
cnc_dial_recess = 6;

usb_hole_width = 15;
usb_hole_height = 8;
usb_hole_bottom_offset = 5;

usb_cable_radius = 4.5 / 2;

nail_head_radius =  6;
nail_shaft_radius = 1.75;
nail_hanger_taper = nail_head_radius + 1;
nail_hanger_drop = nail_head_radius + 12;

eps = 0.05;
eps2 = eps*2;

$fn=64;

// 4 screw holes for the board
// centered 

module board_screw_holes() {

  for(x = [0 : 1]) {
    for(y = [0 : 1]) {
      translate([(-board_width/2) + board_screw_x_offset + (x * board_screw_x_spacing), 
                 (-board_height/2) + board_screw_y_offset_top + (y * board_screw_y_spacing) , 
                 -1]) {
        cylinder(board_screw_depth, board_screw_radius, board_screw_radius, center = true);
      }

      translate([(-board_width/2) + board_screw_x_offset + (x * board_screw_x_spacing), 
                 (-board_height/2) + board_screw_y_offset_top + (y * board_screw_y_spacing) , 
                 -bottom_thickness + eps2]) {
        cylinder(8, 3, 3, center = true);
      }
    }
  }
}

// recess for the board
// includes the USB cable hole

module board_recess() {

    difference() {

        union() {

// hole for the board

              translate([0, 0, 0]) {
                    radiiPoints=[[-board_cover_width/2, -board_cover_height/2, board_cover_radius],
                                [ board_cover_width/2,  -board_cover_height/2, board_cover_radius],
                                [ board_cover_width/2,   board_cover_height/2, board_cover_radius],
                                [-board_cover_width/2,   board_cover_height/2, board_cover_radius],
                                ];
            
                    polyRoundExtrude(radiiPoints, board_cover_thickness, 0, 2, fn=16);
        
              }

// a bit extra thinner for the nail hanger

                 translate([-15, -50, -3]) {
                    cube([30, 25, 3 + eps2]);
                }
        
          }

// subtract out the block for the nail hanger      
     
         translate([-15, -25, 0]) {
            cube([30, 15, 3]);
        }

      
  }    
    
}

// hole for mounting the CNC dial

module cnc_dial_hole() {

  union() {

// hole for the mount, if want recessed

    translate([0, 0, 0]) {
      cylinder(60, cnc_dial_hole_radius, cnc_dial_hole_radius);
    }

// hole for the hookups

    translate([0, 0, -12]) {
      cylinder(60, cnc_dial_hookup_radius, cnc_dial_hookup_radius);
    }

// screw holes
    
    for(a = [0 : 2]) {
      rotate([0, 0, 120 * a]) {
// hole
        translate([-cnc_dial_screw_offset, 0, -main_depth]) { 
          cylinder(60, cnc_dial_screw_radius, cnc_dial_screw_radius);
        }
// nut recess
        translate([-cnc_dial_screw_offset, 0, -main_depth]) { 
          cylinder((main_depth - 5), cnc_dial_nut_radius, cnc_dial_nut_radius);
        }
      }
    }

  }
  
}

// USB port hole

module usb_hole() {
  hull() {
    translate([-(usb_hole_width - usb_hole_height) / 2, 0, 0]) { 
      cylinder(40, usb_hole_height / 2, usb_hole_height / 2);
    }
    translate([(usb_hole_width - usb_hole_height) / 2, 0, 0]) { 
      cylinder(40, usb_hole_height / 2, usb_hole_height / 2);
    }
  }  
}

// usb cable conduit

module usb_conduit() {
  radiiPoints=[
               [ usb_cable_radius - 31, 0,                           10],
               [ usb_cable_radius - 31,20,                   40],
               [ usb_cable_radius - 15, main_height, 40],
               [ usb_cable_radius +  0, main_height+cnc_dial_height - 30, 40],
               [ usb_cable_radius +  0, main_height+cnc_dial_height - 0, 40],
               [-usb_cable_radius +  0, main_height+cnc_dial_height - 0, 40],
               [-usb_cable_radius +  0, main_height+cnc_dial_height - 30, 40],
               [-usb_cable_radius - 15, main_height, 40],
               [-usb_cable_radius - 31, 20,                   40],
               [-usb_cable_radius - 31,     0,                           10],
              ];

  union() {
// main conduit
    polyRoundExtrude(radiiPoints, usb_cable_radius * 2, 2, 1.25, fn=16);

// tabs for cable
  
  }    
    
}

// nail hanger hole

module nail_hanger_hole() {
  radiiPoints=[
               [ -nail_head_radius, -nail_head_radius,                nail_head_radius],
               [  nail_head_radius, -nail_head_radius,                nail_head_radius],
               [  nail_head_radius,  nail_head_radius - 4, nail_head_radius],
               [  nail_shaft_radius + 1, nail_hanger_taper, 4],
               [  nail_shaft_radius, nail_hanger_drop, nail_shaft_radius],
               [ -nail_shaft_radius, nail_hanger_drop, nail_shaft_radius],
               [ -nail_shaft_radius - 1, nail_hanger_taper, 4],
               [ -nail_head_radius,  nail_head_radius - 4, nail_head_radius],
              ];

// make the hole pattern
    polyRoundExtrude(radiiPoints, 30, 0, -2, fn=16);


}


// the main body

module main_body() {
  radiiPoints=[[-main_width/2,     0,                           8],
               [main_width/2,      0,                           8],
               [cnc_dial_width/2,  main_height + cnc_dial_height, 40],
               [-cnc_dial_width/2, main_height + cnc_dial_height, 40],
              ];
    
  polyRoundExtrude(radiiPoints, main_depth, 6, 6, fn=16);
}


union() {

  difference() {    

// start with the main body

      main_body();

    
// recess for the board

    translate([0, board_cover_height/2 + top_padding, bottom_thickness]) {
      rotate([0, 0, 0]) {
        board_recess();
      }
    }
    
// screw holes for the board

    translate([0, board_cover_height/2 + board_edge_spacing + top_padding, bottom_thickness]) {
      rotate([0, 0, 0]) {
        board_screw_holes();
      }
    }      

// USB cable port for the board

    translate([0, 8, bottom_thickness + usb_hole_bottom_offset]) {
      rotate([90, 0, 0]) {
        usb_hole();
      }
    }
    
// recess for the dial

    translate([0, top_padding + main_height + cnc_dial_padding + cnc_dial_hole_radius/2 + 2, main_depth - cnc_dial_recess]) {
      rotate([0, 0, 90]) {
        cnc_dial_hole();  
      }
    }      

// wire chase for the CNC dial
    
    translate([board_width/2 + side_padding - 8 , top_padding + 18 , bottom_thickness + 7]) {
      rotate([90, 0, 0]) {
        cylinder(30, 5, 5, center=true);
      }
    }

    translate([10, board_height + top_padding + cnc_dial_padding/2 + 2, bottom_thickness + 4.5]) {
      rotate([90, 0, 0]) {
        cylinder(cnc_dial_padding + 15, 4.5, 4.5, center=true);
      }
    }
    
// conduit for the USB cable

    translate([ 0, -eps2, -eps2]) {
      usb_conduit();
    }
    
// nail hanger hole
    
    translate([ 0, 35, -eps2]) {
      rotate([0, 0, 180]) {
        nail_hanger_hole();
      }
      
    }
    
// reset button hole

    translate([main_width/2 - 5.1, 19.5 + top_padding + board_overhang + board_edge_spacing, bottom_thickness + board_screw_depth]) {
      rotate([0, 90, 0]) {
        cylinder(10.5, 2, 2, center=true);
      }
    }


  }
  
  
}

