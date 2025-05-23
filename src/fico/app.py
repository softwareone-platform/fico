from textual.app import App
from textual.binding import Binding

from fico.api import FFCOpsClient
from fico.screens.invitation import InvitationDialog
from fico.screens.login import LoginDialog
from fico.screens.main import MainScreen


class Fico(App):
    BINDINGS = [
        Binding(
            "ctrl+x",
            "quit",
            "Exit",
            tooltip="Exit the app and return to the command prompt.",
            show=True,
            priority=True,
        ),
        Binding(
            "l",
            "logout",
            "Logout",
            tooltip="Logout from the app.",
            show=True,
            priority=True,
        ),
    ]
    def __init__(self):
        super().__init__()
        self.api_client = None
        self.theme = "tokyo-night"

    async def on_mount(self):
        self.api_client = FFCOpsClient()
        if await self.api_client.can_connect():
            self.push_screen(MainScreen(self.api_client))
        else:
            self.push_screen(LoginDialog(), self.login_or_quit)

    async def login_or_quit(self, login_data: dict[str, str] | None) -> None:
        if not login_data:
            self.exit(result=False, return_code=-1, message="Login aborted!")
        try:
            await self.api_client.login(
                login_data["url"], # type: ignore
                login_data["email"], # type: ignore
                login_data["password"], # type: ignore
            )
        except Exception as e:
            self.notify(
                severity="error",
                title="Error",
                message=f"Invalid credentials: {e}",
            )
            self.push_screen(LoginDialog(), self.login_or_quit)
            return

        self.push_screen(MainScreen(self.api_client))

    async def action_logout(self) -> None:
        self.pop_screen()
        await self.api_client.logout()
        self.push_screen(LoginDialog(), self.login_or_quit)

    def action_accept_invitation(self) -> None:
        self.app.push_screen(InvitationDialog(new_user=True), self.accept_invitation)

    async def accept_invitation(self, invitation_data: dict[str, str] | None) -> None:
        if not invitation_data:
            return
        try:
            await self.api_client.accept_invitation(
                invitation_data["url"],
                invitation_data["user"],
                invitation_data["token"],
                invitation_data["password"],
            )

            self.notify(
                severity="information",
                title="Success",
                message=f"Invitation for user {invitation_data['user']} successfully accepted",
            )
        except Exception as e:
            self.notify(
                severity="error",
                title="Error",
                message=f"Error accepting invitation: {e}",
            )
            self.push_screen(InvitationDialog(invitation_data), self.accept_invitation)
            return


def app():
    Fico().run()


if __name__ == "__main__":
    app()
