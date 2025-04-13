/* Variable Menu*/
const navMenu = document.getElementById("nav-menu"),
  navToggle = document.getElementById("nav-toggle"),
  navClose = document.getElementById("nav-close");

/* Menu Show */
if (navToggle) {
  navToggle.addEventListener("click", () => {
    navMenu.classList.add("show-menu");
  });
}

/* Menu Hidden */
if (navClose) {
  navClose.addEventListener("click", () => {
    navMenu.classList.remove("show-menu");
  });
}
/* Remove Menu Mobile*/
const navLink = document.querySelectorAll(".nav_link");

const linkAction = () => {
  const navMenu = document.getElementById("nav-menu");
  navMenu.classList.remove("show-menu");
};
navLink.forEach((n) => n.addEventListener("click", linkAction));

/* Contact */
const inputs = document.querySelectorAll(".input");

function focusFunc() {
  let parent = this.parentNode;
  parent.classList.add("focus");
}

function blurFunc() {
  let parent = this.parentNode;
  if (this.value == "") {
    parent.classList.remove("focus");
  }
}

inputs.forEach((input) => {
  input.addEventListener("focus", focusFunc);
  input.addEventListener("blur", blurFunc);
});


// FAQ Toggle on Contact us
document.querySelectorAll('.faq-question').forEach(question => {
    question.addEventListener('click', () => {
        const item = question.parentElement;
        item.classList.toggle('active');
    });
});

// Flash Message Auto Dismiss
document.addEventListener('DOMContentLoaded', function() {
  const flashMessages = document.querySelectorAll('.flash-message');
  flashMessages.forEach(message => {
      setTimeout(() => {
          removeFlashMessage(message);
      }, 5000); // Auto hilang message in 5 second
  });
});

function closeFlashMessage(button) {
  const message = button.closest('.flash-message');
  removeFlashMessage(message);
}

function removeFlashMessage(message) {
  message.classList.add('removing');
  message.addEventListener('animationend', () => {
      message.remove();
  });
}

// No space
// Prevent spaces in username and login inputs
const usernameInput = document.getElementById('username');
const loginInput = document.getElementById('login');
const email = document.getElementById('email');
const password1 = document.getElementById('password1');
const password2 = document.getElementById('password2');
const password = document.getElementById('password');
const phone = document.getElementById('phone');
(usernameInput || loginInput)?.addEventListener('keypress', function(e) {
    if (e.key === ' ') {
        e.preventDefault();
    }
});
(password1 || password)?.addEventListener('keypress', function(e) {
    if (e.key === ' ') {
        e.preventDefault();
    }
});
(password2)?.addEventListener('keypress', function(e) {
    if (e.key === ' ') {
        e.preventDefault();
    }
});
(email)?.addEventListener('keypress', function(e) {
    if (e.key === ' ') {
        e.preventDefault();
    }
});
(phone)?.addEventListener('keypress', function(e) {
    if (e.key === ' ') {
        e.preventDefault();
    }
});