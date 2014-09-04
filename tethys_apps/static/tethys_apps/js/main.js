// Initialize Masonry
var msnry = new Masonry( '#app-list', {
  // options
  columnWidth: 240,
  itemSelector: '.app-container'
});

// Layout Masonry again after all images have loaded
imagesLoaded( container, function() {
  msnry.layout();
});