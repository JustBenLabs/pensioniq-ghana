// ==========================================================
// PENSIONIQ GHANA
// RESET PASSWORD
// ==========================================================


const API_BASE_URL =
    "http://127.0.0.1:8000";


const resetPasswordForm =
    document.getElementById(
        "reset-password-form"
    );


const resetPasswordButton =
    document.getElementById(
        "reset-password-button"
    );


const resetError =
    document.getElementById(
        "reset-error"
    );


const resetSuccess =
    document.getElementById(
        "reset-success"
    );


const invalidResetLink =
    document.getElementById(
        "invalid-reset-link"
    );


// ==========================================================
// READ RESET TOKEN
// ==========================================================

const queryParameters =
    new URLSearchParams(
        window.location.search
    );


const resetToken =
    queryParameters.get(
        "token"
    );


// ==========================================================
// INVALID / MISSING TOKEN
// ==========================================================

if (
    !resetToken
    ||
    !resetToken.trim()
) {

    invalidResetLink.classList.remove(
        "hidden"
    );


    resetPasswordForm.classList.add(
        "hidden"
    );

}


// ==========================================================
// SUBMIT
// ==========================================================

resetPasswordForm.addEventListener(
    "submit",
    resetPassword
);


async function resetPassword(
    event
) {

    event.preventDefault();


    hideMessages();


    if (!resetToken) {

        showError(
            "Password-reset token is missing."
        );

        return;

    }


    const newPassword =
        document.getElementById(
            "new-password"
        ).value;


    const confirmPassword =
        document.getElementById(
            "confirm-password"
        ).value;


    if (
        newPassword.length < 8
    ) {

        showError(
            "Your new password must contain at least 8 characters."
        );

        return;

    }


    if (
        newPassword !==
        confirmPassword
    ) {

        showError(
            "The passwords do not match."
        );

        return;

    }


    setLoading(
        true
    );


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/auth/reset-password`,
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            {

                                token:
                                    resetToken,

                                new_password:
                                    newPassword

                            }
                        )

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                getApiErrorMessage(
                    data,
                    "Unable to reset your password."
                )
            );

        }


        resetPasswordForm.reset();


        resetPasswordForm.classList.add(
            "hidden"
        );


        showSuccess(
            data.message
            ||
            (
                "Password reset successfully. "
                +
                "Redirecting you to sign in..."
            )
        );


        // Remove reset token from address bar.

        window.history.replaceState(
            {},
            document.title,
            "reset-password.html"
        );


        setTimeout(
            () => {

                window.location.href =
                    "login.html";

            },
            1800
        );

    }

    catch (error) {

        showError(
            error.message
        );

    }

    finally {

        setLoading(
            false
        );

    }

}


// ==========================================================
// HELPERS
// ==========================================================

function setLoading(
    loading
) {

    resetPasswordButton.disabled =
        loading;


    resetPasswordButton.textContent =
        loading
        ?
        "Resetting Password..."
        :
        "Reset Password";

}


function showError(
    message
) {

    resetError.textContent =
        message;


    resetError.classList.remove(
        "hidden"
    );


    resetSuccess.classList.add(
        "hidden"
    );

}


function showSuccess(
    message
) {

    resetSuccess.textContent =
        message;


    resetSuccess.classList.remove(
        "hidden"
    );


    resetError.classList.add(
        "hidden"
    );

}


function hideMessages() {

    resetError.textContent =
        "";


    resetSuccess.textContent =
        "";


    resetError.classList.add(
        "hidden"
    );


    resetSuccess.classList.add(
        "hidden"
    );

}


function getApiErrorMessage(
    data,
    fallback
) {

    if (
        data
        &&
        typeof data.detail
        ===
        "string"
    ) {

        return data.detail;

    }


    if (
        data
        &&
        Array.isArray(
            data.detail
        )
    ) {

        return data.detail
            .map(
                item =>
                    item.msg
                    ||
                    "Invalid information"
            )
            .join(" ");

    }


    return fallback;

}