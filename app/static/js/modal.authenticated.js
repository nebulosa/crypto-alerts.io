const account  = document.querySelector("#account")
const settings = document.querySelector("#settings")

const modalAccount             = document.querySelector("#modal-account")
const modalAccountEditEmail    = document.querySelector("#modal-account-edit-email")
const modalAccountEditPassword = document.querySelector("#modal-account-edit-password")
const modalAccountDelete       = document.querySelector("#modal-account-delete")
const modalAlertDelete         = document.querySelector("#modal-alert-delete")
const modalSettings            = document.querySelector("#modal-settings")

const modalBackground = document.querySelectorAll(".modal-background")

account.addEventListener('click', () => {
  modalAccount.classList.add('is-active')
})

settings.addEventListener('click', () => {
  modalSettings.classList.add('is-active')
})

function disableAllModals() {
  modalAccount.classList.remove('is-active')
  modalAccountEditEmail.classList.remove('is-active')
  modalAccountEditPassword.classList.remove('is-active')
  modalAccountDelete.classList.remove('is-active')

  if(modalAlertDelete) {
    modalAlertDelete.classList.remove('is-active')
  }

  modalSettings.classList.remove('is-active')
}

function gotoAccountEditEmailModal() {
  disableAllModals()
  modalAccountEditEmail.classList.add('is-active')
}

function gotoAccountEditPasswordModal() {
  disableAllModals()
  modalAccountEditPassword.classList.add('is-active')
}

function gotoAccountDeleteModal() {
  disableAllModals()
  modalAccountDelete.classList.add('is-active')
}

function gotoAlertDeleteModal(id) {
  disableAllModals()
  modalAlertDelete.classList.add('is-active')
  var link = document.getElementById('modal-alert-delete-link')
  if (link) { //replace dump link with the actual alert id
    //  in  => https://domain.tld/alert/delete/dumb
    //  out => https://domain.tld/alert/delete/a1624b05f6a0c71d70921b5582825756
    link.href = link.href.replace(/\/[^\/]*$/, '/' + id)
  }
}

modalBackground.forEach(item => {
  item.addEventListener('click', event => {
    disableAllModals()
  })
})
