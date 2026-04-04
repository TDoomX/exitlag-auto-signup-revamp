import requests
import sys
import re
from DrissionPage import ChromiumPage


# Author: Doom
# GitHub: https://github.com/TDoomX


class Main:
    def checkPassword(self, password):
        hasLowercase = re.search(r'[a-z]', password)
        hasUppercase = re.search(r'[A-Z]', password)
        hasSpecial = re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        hasNumber = re.search(r'[0-9]', password)

        if (len(password) >= 8 and
                hasLowercase and
                hasUppercase and
                hasSpecial and
                hasNumber):
            return "\nPassword is valid."
        else:
            if len(password) < 8:
                return "\nPassword does not meet the requirements. Please use at least 8 characters."
            if not hasLowercase:
                return "\nPassword does not meet the requirements. Please use a lowercase letter."
            if not hasUppercase:
                return "\nPassword does not meet the requirements. Please use an uppercase letter."
            if not hasSpecial:
                return "\nPassword does not meet the requirements. Please use at least 1 special character (!@#$%^&*(),.?\":{}|<>)."
            if not hasNumber:
                return "\nPassword does not meet the requirements. Please use at least 1 number."

    def checkUpdate(self):
        try:
            resp = requests.get(
                "https://api.github.com/repos/TDoomX/exitlag-auto-signup-revamp/releases/latest",
                timeout=5
            )
            resp.raise_for_status()
            latestVer = resp.json()["tag_name"]

            with open("version.txt", "r") as file:
                currentVer = file.read().strip()

            if currentVer < latestVer:
                print(f"Update available: {latestVer} (Current: {currentVer})")
                print(f"Download: https://github.com/TDoomX/exitlag-auto-signup-revamp/releases/latest")
            else:
                print(f"You are running the latest version: {currentVer}")

        except Exception as e:
            print(f"Could not check for updates: {e}")

    def testProxy(self, proxy):
        try:
            response = requests.get(
                "http://www.google.com",
                proxies={"http": proxy, "https": proxy},
                timeout=5
            )
            return True, response.status_code
        except Exception:
            return False, "Proxy test failed! Please ensure that the proxy is working correctly. Skipping proxy usage..."


if __name__ == "__main__":
    print("This is a library file. Please run main.py instead.")
