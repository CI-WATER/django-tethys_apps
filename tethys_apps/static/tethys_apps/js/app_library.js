/*****************************************************************************
 * FILE:      Tethys App Library Module
 * DATE:      6 September 2014
 * AUTHOR:    Nathan Swain
 * COPYRIGHT: (c) 2014 Brigham Young University
 * LICENSE:   BSD 2-Clause
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var TETHYS_APPS_LIBRARY = (function() {
	// Wrap the library in a package function
	"use strict"; // And enable strict mode for this library

	/************************************************************************
 	*                      MODULE LEVEL / GLOBAL VARIABLES
 	*************************************************************************/
 	var public_interface,   // The public interface object that is returned by the module
 	    msnry,              // Global masonry object
 	    app_list_container, // Container with the app items in it
 	    app_item_selector;  // App item selector



	/************************************************************************
 	*                    PRIVATE FUNCTION DECLARATIONS
 	*************************************************************************/
 	var launch_app;


 	/************************************************************************
 	*                    PRIVATE FUNCTION IMPLEMENTATIONS
 	*************************************************************************/

 	launch_app = function(element, url) {
 	    // Declare variables
 	    var delay_ms, delay_s, delay_s_string, secondary_margin_bottom;

 	    // Assign variables
 	    delay_s = 0.8;             // seconds
 	    delay_ms = delay_s * 1000; // milliseconds
 	    delay_s_string = delay_s.toString() + 's';
 	    secondary_margin_bottom = parseInt($('.tethys-secondary-header').css('margin-bottom')) + 300;


 	    // Delay loading app to allow transition
        setTimeout(function(){
          // Redirect to app home page
          window.location = url;
        }, delay_ms);

        // Hide the headers
        $('.header-wrapper').css('transition', 'margin ' + delay_s_string + ' ease');
        $('.header-wrapper').css('margin-top', '-90px');
        $('.tethys-secondary-header').css('transition', 'margin ' + delay_s_string + ' ease');
        $('.tethys-secondary-header').css('margin-top', '-300px');
        $('.tethys-secondary-header').css('margin-bottom', secondary_margin_bottom.toString() + 'px');

        // Adjust element
        $(element).css('z-index', 300);

        // Drop the curtain
        $('#app-library-curtain').addClass('show');

        // Hide the element
        $(element).addClass('fade-prep');
        $(element).addClass('fade-out');


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
		  launch_app: launch_app
	};

	/************************************************************************
 	*                  INITIALIZATION / CONSTRUCTOR
 	*************************************************************************/

	// Initialization: jQuery function that gets called when
	// the DOM tree finishes loading
	$(function() {
	    // Get a handle on the app items container
	    app_list_container = document.getElementById('app-list')
	    app_item_selector = '.app-container'

	    // The Tethys apps library page uses masonry.js to accomplish the Pinterest-like stacking of the app icons
        msnry = new Masonry( app_list_container, {
          // options
          columnWidth: 240,
          itemSelector: app_item_selector
        });

        // If the app icon images take some time to load, it may mess up the masonry formatting. This modules uses the
        // imagesloaded.js project to reformat the masonry after all the images have loaded.
        imagesLoaded( app_list_container, function() {
          msnry.layout();
        });
	});

	return public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed, returning the public interface object.