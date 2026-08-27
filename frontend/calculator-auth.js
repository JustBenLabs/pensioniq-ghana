/// ==========================================================
// PENSIONIQ GHANA
// RETIREMENT CALCULATOR AUTHENTICATION
// ==========================================================

const CALCULATOR_TOKEN_KEY =
    "pensioniq_access_token";


async function verifyCalculatorAccess() {

    const token =
        sessionStorage.getItem(
            CALCULATOR_TOKEN_KEY
        );


    if (!token) {

        window.location.replace(
            "login.html"
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${window.PENSIONIQ_API_BASE_URL}/auth/me`,
                {
                    headers: {
                        Authorization:
                            `Bearer ${token}`
                    }
                }
            );


        if (!response.ok) {

            throw new Error(
                "Invalid session."
            );

        }


        // Authentication succeeded.
        // Reveal the calculator.

        document.documentElement
            .classList.remove(
                "auth-pending"
            );


        // Only now load the calculator application.

        const appScript =
            document.createElement(
                "script"
            );

        appScript.src =
            "app.js";


        document.body.appendChild(
            appScript
        );

    }
    catch (error) {

        sessionStorage.removeItem(
            CALCULATOR_TOKEN_KEY
        );


        window.location.replace(
            "login.html"
        );

    }

}


verifyCalculatorAccess();