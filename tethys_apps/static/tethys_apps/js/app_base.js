/*****************************************************************************
 * FILE:      Tethys App Base Module
 * DATE:      6 September 2014
 * AUTHOR:    Nathan Swain
 * COPYRIGHT: (c) 2014 Brigham Young University
 * LICENSE:   BSD 2-Clause
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var TETHYS_APP_BASE = (function() {
	// Wrap the library in a package function
	"use strict"; // And enable strict mode for this library

	/************************************************************************
 	*                      MODULE LEVEL / GLOBAL VARIABLES
 	*************************************************************************/
 	var public_interface,   // The public interface object that is returned by the module
 	    wrapper_selector;   // String selector used to apply the "show-nav" class



	/************************************************************************
 	*                    PRIVATE FUNCTION DECLARATIONS
 	*************************************************************************/
 	var apply_content_height, toggle_nav;


 	/************************************************************************
 	*                    PRIVATE FUNCTION IMPLEMENTATIONS
 	*************************************************************************/


 	toggle_nav = function() {
        if ($(wrapper_selector).hasClass('show-nav')) {
            // Do things on Nav Close
            $(wrapper_selector).removeClass('show-nav');
        } else {
            // Do thing on Nav Open
            $(wrapper_selector).addClass('show-nav');
        }
 	};

 	apply_content_height = function() {
 	    // Declare variables
 	    var app_actions_height, content_height, header_height, window_height;

 	    // Remove height property on wrapper
 	    $(wrapper_selector).css('height', 'auto');

 	    content_height = parseInt($('#app-content').css('height'));
 	    window_height = window.innerHeight;

 	    if (content_height <= window_height) {
 	      // Set the height to 100%
 	      console.log(wrapper_selector);
 	      $(wrapper_selector).css('height', '100%');
 	    } else {
          // Set the height to auto
          $(wrapper_selector).css('height', 'auto');

 	    }
 	};

	/************************************************************************
 	*                        DEFINE PUBLIC INTERFACE
 	*************************************************************************/
	/*
	 * Library object that contains public facing functions of the package.
	 * This is the object that is returned by the library wrapper function.
	 * See below.
	 * NOTE: The functions in the public interface have access to the private
	 * functions of the library because of JavaScript function scope.
	 */
	public_interface = {
		toggle_nav: toggle_nav,
	};

	/************************************************************************
 	*                  INITIALIZATION / CONSTRUCTOR
 	*************************************************************************/

	// Initialization: jQuery function that gets called when
	// the DOM tree finishes loading
	$(function() {
	    // Initialize globals
	    wrapper_selector = '#app-content-wrapper';

        // Bind toggle_nav to the click event of ".toggle-nav" element
        $('.toggle-nav').click(function() {
            public_interface.toggle_nav();
            apply_content_height();
        });

        // Bind to the window resize event
        window.onresize = function() {
          apply_content_height();
        }

        // Run the content is tall check
	    apply_content_height();

	});

	return public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed, returning the public interface object.