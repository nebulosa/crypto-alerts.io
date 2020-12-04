const register = document.querySelector("#register")
const login    = document.querySelector("#login")

const modalRegister = document.querySelector("#modal-register")
const modalLogin    = document.querySelector("#modal-login")
const modalRecover  = document.querySelector("#modal-recover-account")

const modalBackground = document.querySelectorAll(".modal-background")

register.addEventListener('click', () => {
  modalRegister.classList.add('is-active');
});

login.addEventListener('click', () => {
  modalLogin.classList.add('is-active');
});

modalBackground.forEach(item => {
  item.addEventListener('click', event => {
    modalLogin.classList.remove('is-active');
    modalRegister.classList.remove('is-active');
    modalRecover.classList.remove('is-active');
  })
});

function gotoRegisterModal() {
  modalLogin.classList.remove('is-active');
  modalRecover.classList.remove('is-active');
  modalRegister.classList.add('is-active');
}

function gotoLoginModal() {
  modalRecover.classList.remove('is-active');
  modalRegister.classList.remove('is-active');
  modalLogin.classList.add('is-active');
}

function gotoRecoverModal() {
  modalRegister.classList.remove('is-active');
  modalLogin.classList.remove('is-active');
  modalRecover.classList.add('is-active');
}
