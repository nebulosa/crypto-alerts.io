const register = document.querySelector("#register")
const login    = document.querySelector("#login")

const modalRegister = document.querySelector("#modal-register")
const modalLogin    = document.querySelector("#modal-login")
const modalRecover  = document.querySelector("#modal-recover-account")

const modalBackground = document.querySelectorAll(".modal-background")

register.addEventListener('click', () => {
  modalRegister.classList.add('is-active')
})

login.addEventListener('click', () => {
  modalLogin.classList.add('is-active')
})

function disableAllModals() {
  modalLogin.classList.remove('is-active')
  modalRecover.classList.remove('is-active')
  modalRegister.classList.remove('is-active')
}

function gotoRegisterModal() {
  disableAllModals()
  modalRegister.classList.add('is-active')
}

function gotoLoginModal() {
  disableAllModals()
  modalLogin.classList.add('is-active')
}

function gotoRecoverModal() {
  disableAllModals()
  modalRecover.classList.add('is-active')
}

modalBackground.forEach(item => {
  item.addEventListener('click', event => {
    disableAllModals()
  })
})
