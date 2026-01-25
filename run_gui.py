#!/usr/bin/env python3
"""
Launch QB-Assistant GUI for parameter configuration.
"""

import os
from src.gui.app import App
from src.gui.forms.sample_params_form import SampleParamsForm
from src.gui.forms.budget_params_form import BudgetParamsForm
from src.gui.forms.main_menu_form import MainMenuForm
from src.gui.forms.client_selection_form import ClientSelectionForm

def main():
    app = App('/home/max/projects/QB-Assistant')

    # Enforce client selection prerequisite
    if app.selected_client is None:
        app.show_form(ClientSelectionForm)
    else:
        app.show_form(MainMenuForm)

    app.mainloop()


if __name__ == "__main__":
	main()