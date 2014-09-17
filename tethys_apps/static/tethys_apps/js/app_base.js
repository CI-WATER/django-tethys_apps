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
 	var public_interface,         // The public interface object that is returned by the module
 	    apps_library_url,         // The relative url of the apps library page
 	    app_header_selector,      // String selector for the app header element
 	    app_content_selector,     // String selector for the app content element
 	    wrapper_selector,         // String selector for the app wrapper element
 	    toggle_nav_selector,      // String selector for the toggle nav element
 	    app_navigation_selector;  // String selector for the app navigation element



	/************************************************************************
 	*                    PRIVATE FUNCTION DECLARATIONS
 	*************************************************************************/
 	var apply_content_height, app_entry_handler, no_nav_handler, toggle_nav;


 	/************************************************************************
 	*                    PRIVATE FUNCTION IMPLEMENTATIONS
 	*************************************************************************/

    // Handle toggling nav effects
 	toggle_nav = function() {
 	    // Add the with-transition class if not present
 	    if ( !$(wrapper_selector).hasClass('with-transition') ) {
 	        $(wrapper_selector).addClass('with-transition');
 	    }

 	    // Toggle the show-nav class
        if ($(wrapper_selector).hasClass('show-nav')) {
            // Do things on Nav Close
            $(wrapper_selector).removeClass('show-nav');
            $(toggle_nav_selector).css('width', '20px');
            $(toggle_nav_selector).css('margin-right', '0');

        } else {
            // Do thing on Nav Open
            $(wrapper_selector).addClass('show-nav');
            $(toggle_nav_selector).css('width', '15px');
            $(toggle_nav_selector).css('margin-right', '5px');

        }
 	};

 	// Handle the entry entry transitions in the app
 	app_entry_handler = function() {
 	    // Declare vars
 	    var  referrer_no_protocol, referrer_no_host;

 	    // Get the referrer url and strip off protocol
 	    referrer_no_protocol = document.referrer.split('//')[1];

        // Check if referrer exists and it contains our host
 	    if (referrer_no_protocol && referrer_no_protocol.indexOf(location.host) > -1) {
            referrer_no_host = referrer_no_protocol.replace(location.host, '');

            // If the referrer was the app library, add transition classes to create a
            // smooth transition effect on app launch
            if (referrer_no_host === apps_library_url) {
                $(app_header_selector).addClass('with-transition');
                $(app_content_selector).addClass('with-transition');
            }
 	    }

        // Add the "show" classes appropriately to show things that are hidden by default
 	    $(app_header_selector).addClass('show-header');
 	    $(app_content_selector).addClass('show-app-content');
 	};

 	// Handle case when there is no nav present
 	no_nav_handler = function() {
 	    // If no nav present...
        if ( !$(app_navigation_selector).length ) {
            // Hide the nav area
            $('#app-content').css('transition', 'none');
            $(wrapper_selector).removeClass('show-nav');

            // Hide the toggle button and then remove it
            $(toggle_nav_selector).css('display', 'none');
            $(toggle_nav_selector).remove();
        }
 	};

    // Handle changes in app content height
 	apply_content_height = function() {
 	    // Declare variables
 	    var app_actions_height, content_height, header_height, window_height;

 	    // Remove height property on wrapper so our measurement isn't biased
 	    $(wrapper_selector).css('height', 'auto');

        // Measure the content height and the window height for comparison
 	    content_height = parseInt($('#app-content').css('height'));
 	    window_height = window.innerHeight;

        // If the content height is less than the window height...
 	    if (content_height <= window_height) {
 	      // Set the height to 100% so the content fills the window
 	      $(wrapper_selector).css('height', '100%');

 	    } else {
          // Otherwise, set the height to auto so that it overflows appropriately
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
	    apps_library_url = '/apps/';
	    app_header_selector = '.tethys-app-header';
 	    app_content_selector = '#app-content';
	    wrapper_selector = '#app-content-wrapper';
	    toggle_nav_selector = '.toggle-nav';
	    app_navigation_selector = '#app-navigation';

        // Bind toggle_nav to the click event of ".toggle-nav" element
        $(toggle_nav_selector).click(function() {
            public_interface.toggle_nav();
            apply_content_height();
        });

        // Bind to the window resize event
        window.onresize = function() {
          apply_content_height();
        }

        // Adjust content height accordingly
	    apply_content_height();

	    // Run no nav handler
	    no_nav_handler();

	    // Run the app entry handler
	    app_entry_handler();

	});

	return public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed, returning the public interface object.