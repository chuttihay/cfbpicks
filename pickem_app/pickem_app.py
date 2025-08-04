# app.py
import reflex as rx

class State(rx.State):
    sidebar_open: bool = False

    def toggle_sidebar(self):
        self.sidebar_open = not self.sidebar_open

def navbar():
    return rx.hstack(
        rx.button(
            rx.icon("menu"),
            on_click=State.toggle_sidebar,
            variant="ghost",
            size="4"
        ),
        rx.text("College Football App", font_size="xl", font_weight="bold"),
        justify="between",
        align="center",
        padding="1rem",
        bg="blue.600",
        color="white",
        width="100%",
        position="fixed",
        top="0",
        z_index="1000"
    )

def sidebar():
    return rx.box(
        rx.vstack(
            rx.link("Standings", href="/", font_size="lg", padding="0.5rem"),
            rx.link("Teams", href="/teams", font_size="lg", padding="0.5rem"),
            rx.link("My Picks", href="/picks", font_size="lg", padding="0.5rem"),
            rx.link("Rules", href="/standings", font_size="lg", padding="0.5rem"),
            spacing="4"
        ),
        bg="gray.100",
        width="250px",
        height="100vh",
        position="fixed",
        top="0",
        left="0",
        transform=rx.cond(State.sidebar_open, "translateX(0)", "translateX(-100%)"),
        transition="transform 0.3s ease-in-out",
        z_index="999"
    )

def index():
    return rx.box(
        sidebar(),
        navbar(),
        rx.box(
            rx.text("2025 College Football Pick'em!"),
            padding_top="4rem",
            padding="2rem"
        )
    )

app = rx.App()
app.add_page(index, route="/")

