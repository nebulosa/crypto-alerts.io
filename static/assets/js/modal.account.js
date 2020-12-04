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
  modalAccount.classList.add('is-active');
});

settings.addEventListener('click', () => {
  modalSettings.classList.add('is-active');
});

modalBackground.forEach(item => {
  item.addEventListener('click', event => {
    modalAccount.classList.remove('is-active');
    modalAccountEditEmail.classList.remove('is-active');
    modalAccountEditPassword.classList.remove('is-active');
    modalAccountDelete.classList.remove('is-active');

    modalAlertDelete.classList.remove('is-active');

    modalSettings.classList.remove('is-active');
  })
});

function gotoAccountEditEmailModal() {
  modalAccount.classList.remove('is-active');
  modalAccountEditPassword.classList.remove('is-active');
  modalAccountDelete.classList.remove('is-active');
  modalSettings.classList.remove('is-active');
  modalAlertDelete.classList.remove('is-active');

  modalAccountEditEmail.classList.add('is-active');
}

function gotoAccountEditPasswordModal() {
  modalAccount.classList.remove('is-active');
  modalAccountEditEmail.classList.remove('is-active');
  modalAccountDelete.classList.remove('is-active');
  modalAlertDelete.classList.remove('is-active');
  modalSettings.classList.remove('is-active');

  modalAccountEditPassword.classList.add('is-active');
}

function gotoAccountDeleteModal() {
  modalAccount.classList.remove('is-active');
  modalAccountEditEmail.classList.remove('is-active');
  modalAccountEditPassword.classList.remove('is-active');
  modalSettings.classList.remove('is-active');
  modalAlertDelete.classList.remove('is-active');

  modalAccountDelete.classList.add('is-active');
}

function gotoAlertDeleteModal() {
  modalAccount.classList.remove('is-active');
  modalAccountDelete.classList.remove('is-active');
  modalAccountEditEmail.classList.remove('is-active');
  modalAccountEditPassword.classList.remove('is-active');
  modalSettings.classList.remove('is-active');

  modalAlertDelete.classList.add('is-active');
}
