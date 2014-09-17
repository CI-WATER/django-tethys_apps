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
 	    wrapper_selector,         // String selector used to apply the "show-nav" class
 	    toggle_nav_selector,      // String selector used to bind to the toggle nav element
 	    app_navigation_selector;  // String selector used to app navigation selector



	/************************************************************************
 	*                    PRIVATE FUNCTION DECLARATIONS
 	*************************************************************************/
 	var apply_content_height, header_entry_handler, no_nav_handler, toggle_nav;


 	/************************************************************************
 	*                    PRIVATE FUNCTION IMPLEMENTATIONS
 	*************************************************************************/

    // Handle toggling nav effects
 	toggle_nav = function() {
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

 	// Handle the header entry mode
 	header_entry_handler = function() {
 	    // Declare vars
 	    var  app_header_selector, referrer_no_protocol, referrer_no_host;

 	    // Assign vars
 	    app_header_selector = '.tethys-app-header';

 	    // Get the referrer url and strip off protocol
 	    referrer_no_protocol = document.referrer.split('//')[1];

        // Check if referrer exists and it contains our host
 	    if (referrer_no_protocol && referrer_no_protocol.indexOf(location.host) > -1) {
            referrer_no_host = referrer_no_protocol.replace(location.host, '');

            // If the referrer was the app library, add transition class to make slide down effect
            if (referrer_no_host === apps_library_url) {
                $(app_header_selector).addClass('show-header-transition');
            }
 	    }

        // Show the header always
 	    $(app_header_selector).addClass('show-header');
 	};

 	// Handle case when there is no nav present
 	no_nav_handler = function() {
 	    // If no nav present...
        if ( !$(app_navigation_selector).length ) {
            // Hide the nav area
            $('#app-content').css('transition', 'none');
            $(wrapper_selector).removeClass('show-nav');

            // Hide the toggle button and remove
            $(toggle_nav_selector).css('display', 'none');
            $(toggle_nav_selector).remove();
        }
 	};

    // Handle changes in app content height
 	apply_content_height = function() {
 	    // Declare variables
 	    var app_actions_height, content_height, header_height, window_height;

 	    // Remove height property on wrapper
 	    $(wrapper_selector).css('height', 'auto');

 	    content_height = parseInt($('#app-content').css('height'));
 	    window_height = window.innerHeight;

 	    if (content_height <= window_height) {
 	      // Set the height to 100%
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
	    apps_library_url = '/apps/';
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

        // Run the content is tall check
	    apply_content_height();

	    // Run the app nav handler
	    no_nav_handler();

	    // Run the header entry handler
	    header_entry_handler();

	});

	return public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed, returning the public interface object.