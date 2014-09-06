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
 	var hello_world;


 	/************************************************************************
 	*                    PRIVATE FUNCTION IMPLEMENTATIONS
 	*************************************************************************/

 	hello_world = function() {
 		console.log("Hello, World!");
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
		hello_goodbye: function() {
			hello_world();
		}
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