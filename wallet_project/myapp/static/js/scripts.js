$(document).ready(function() {
    // Handle Like button click with AJAX
    $('form.like-post').on('submit', function(event) {
        event.preventDefault();

        var form = $(this);
        var postId = form.data('post-id');

        $.ajax({
            type: 'POST',
            url: '/like/' + postId + '/',
            data: {
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
            },
            success: function(response) {
                alert('Post liked successfully!');
                // Optionally update like count or button text here
            }
        });
    });

    // Handle comment submission with AJAX
    $('form.comment-form').on('submit', function(event) {
        event.preventDefault();

        var form = $(this);
        var postId = form.data('post-id');
        var content = form.find('textarea').val();

        $.ajax({
            type: 'POST',
            url: '/comment/' + postId + '/',
            data: {
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val(),
                'content': content,
            },
            success: function(response) {
                alert('Comment posted successfully!');
                location.reload(); // Reload the page to show new comment
            }
        });
    });
});
$(document).ready(function() {
    // Event listener for category filtering
    $('ul.categories-list li a').on('click', function(event) {
        event.preventDefault();
        var categoryId = $(this).data('category-id');

        // Perform an AJAX request to get posts from the selected category
        $.ajax({
            type: 'GET',
            url: '/category/' + categoryId + '/',
            success: function(response) {
                $('#posts-container').html(response);
            }
        });
    });
});

// Example: form validation for signup/login
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');

    form.addEventListener('submit', function(event) {
        let valid = true;
        const inputs = form.querySelectorAll('input');

        inputs.forEach(input => {
            if (input.value.trim() === '') {
                valid = false;
                input.style.borderColor = 'red';
            } else {
                input.style.borderColor = '';
            }
        });

        if (!valid) {
            event.preventDefault();
            alert("Please fill out all fields.");
        }
    });
});

let currentIndex = 0;
const slides = document.querySelectorAll('.slide');
const totalSlides = slides.length;

function showSlide(index) {
    const offset = -100 * index;
    document.querySelector('.slider').style.transform = `translateX(${offset}%)`;
}

function nextSlide() {
    currentIndex = (currentIndex + 1) % totalSlides;
    showSlide(currentIndex);
}

setInterval(nextSlide, 3000); // Change slide every 3 seconds