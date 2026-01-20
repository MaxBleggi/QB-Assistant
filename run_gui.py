#!/usr/bin/env python3
"""
Launch QB-Assistant GUI for parameter configuration.
"""

import os
from src.gui.app import App
from src.gui.forms.sample_params_form import SampleParamsForm
from src.gui.app import App
from src.gui.forms.budget_params_form import BudgetParamsForm

def main():
    app = App('/home/max/projects/QB-Assistant')
    app.show_form(BudgetParamsForm)
    app.mainloop()


if __name__ == "__main__":
	main()