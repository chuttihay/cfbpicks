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
        rx.image(
            src="/ncaa.jpg",
            height="2em",  # adjust as needed
        ),
        rx.text("2025 College Footbal Pick'em", font_size="xl", font_weight="bold"),
        justify="between",
        align="center",
        padding="0.5rem",
        bg=rx.color("white"),
        color=rx.color("white"),
        width="100%",
        position="fixed",
        top="0",
        z_index="1000"
    )


def sidebar():
    links = [
        ("Standings", "/"),
        ("Teams", "/teams"),
        ("My Picks", "/picks"),
        ("Rules", "/rules"),
    ]

    return rx.box(
        rx.vstack(
            rx.box(
                rx.text("🏈 Menu", font_size="2xl", font_weight="bold"),
                padding="1rem",
                width="100%",  # full width
                text_align="center",
            ),
            *[
                rx.box(
                    rx.link(
                        text,
                        href=href,
                        font_size="lg",
                        width="100%",      # full width link container
                        text_align="center",
                        display="block",   # make link block level to fill box
                        padding="0.75rem 0",  # vertical padding
                        on_click=State.toggle_sidebar,
                    ),
                    border_top="1px solid gray",
                    border_bottom="1px solid gray",
                    width="100%",           # full width box to span sidebar
                )
                for text, href in links
            ],
            spacing="0",
            width="100%",  # make vstack full width
        ),
        bg=rx.color("gray", 4),   # darker background for contrast
        width="250px",
        height="100vh",
        position="fixed",
        top="0",
        left="0",
        transform=rx.cond(State.sidebar_open, "translateX(0)", "translateX(-100%)"),
        transition="transform 0.3s ease-in-out",
        z_index="999",
    )


def layout(*children):
    return rx.box(
        sidebar(),
        navbar(),
        rx.box(
            *children,
            # padding_top="4rem",
            padding="4rem 2rem 2rem 2rem",
            margin_left=rx.cond(State.sidebar_open, "250px", "0px"),
            transition="margin-left 0.3s ease-in-out"
        )
    )



def standings_page():
    return layout(
        rx.heading("Standings", size="5"),
        rx.text("This will display current team standings.")
    )

def teams_page():
    return layout(
        rx.heading("Teams", size="4"),
        rx.text("This will show all available teams.")
    )

def picks_page():
    return layout(
        rx.heading("My Picks", size="4"),
        rx.text("This will display the user's current picks.")
    )

def rules_page():
    return layout(
        rx.heading("Rules", size="4"),
        rx.text("This page will show scoring rules and tier breakdowns.")
    )

app = rx.App()
app.add_page(standings_page, route="/", title="Standings")
app.add_page(teams_page, route="/teams", title="Teams")
app.add_page(picks_page, route="/picks", title="My Picks")
app.add_page(rules_page, route="/rules", title="Rules")


