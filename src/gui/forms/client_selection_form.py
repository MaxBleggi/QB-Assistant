"""
Client selection form for client management UI.

Provides CRUD operations for client folders with list view, creation dialog,
selection, and deletion. Acts as prerequisite flow before main menu access.
"""
import tkinter as tk
from tkinter import messagebox, simpledialog


class ClientSelectionForm(tk.Frame):
    """
    Form for managing client selection with CRUD operations.

    Displays client list in Listbox, provides buttons for Create/Select/Delete,
    and navigates to MainMenuForm after client selection.
    """

    def __init__(self, parent):
        """
        Initialize client selection form.

        Args:
            parent: Parent widget (should be App instance with get_client_manager and show_form methods)
        """
        super().__init__(parent)
        self.parent = parent

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Create title label
        title = tk.Label(
            self,
            text="Client Selection",
            font=('Arial', 16, 'bold')
        )
        title.grid(row=0, column=0, columnspan=2, pady=20)

        # Create subtitle/description
        subtitle = tk.Label(
            self,
            text="Select a client to work with, or create a new client",
            font=('Arial', 12),
            fg='#666'
        )
        subtitle.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # Create container for list and buttons
        container = tk.Frame(self)
        container.grid(row=2, column=0, columnspan=2, sticky='nsew', padx=20, pady=10)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=0)

        # Create listbox for clients (left side)
        list_frame = tk.LabelFrame(
            container,
            text="Available Clients",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        list_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))

        # Scrollbar for listbox
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox widget
        self.client_listbox = tk.Listbox(
            list_frame,
            width=30,
            height=15,
            font=('Arial', 10),
            yscrollcommand=scrollbar.set
        )
        self.client_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.client_listbox.yview)

        # Create buttons frame (right side)
        buttons_frame = tk.Frame(container)
        buttons_frame.grid(row=0, column=1, sticky='n')

        # Create Client button
        create_btn = tk.Button(
            buttons_frame,
            text="Create Client",
            command=self.on_create_clicked,
            width=18,
            bg='#4CAF50',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        create_btn.pack(pady=5)

        # Select Client button
        select_btn = tk.Button(
            buttons_frame,
            text="Select Client",
            command=self.on_select_clicked,
            width=18,
            bg='#2196F3',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        select_btn.pack(pady=5)

        # Delete Client button
        delete_btn = tk.Button(
            buttons_frame,
            text="Delete Client",
            command=self.on_delete_clicked,
            width=18,
            bg='#F44336',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        delete_btn.pack(pady=5)

        # Exit button
        exit_btn = tk.Button(
            buttons_frame,
            text="Exit",
            command=self.on_exit_clicked,
            width=18,
            bg='#9E9E9E',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        exit_btn.pack(pady=5)

        # Status message label
        self.status_label = tk.Label(
            self,
            text="",
            font=('Arial', 10),
            fg='#666'
        )
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)

        # Load clients on initialization
        self.refresh_list()

    def refresh_list(self) -> None:
        """
        Refresh listbox with current clients from filesystem.

        Clears listbox and repopulates with discovered client names.
        """
        # Clear listbox
        self.client_listbox.delete(0, tk.END)

        # Discover clients
        try:
            client_mgr = self.parent.get_client_manager()
            clients = client_mgr.discover_clients(self.parent.project_root)

            # Add client names to listbox
            for client in clients:
                self.client_listbox.insert(tk.END, client)

            # Update status
            count = len(clients)
            if count > 0:
                self.status_label.config(text=f"{count} client(s) found", fg='#4CAF50')
            else:
                self.status_label.config(text="No clients yet. Create your first client!", fg='#666')

        except Exception as e:
            self.status_label.config(text=f"Error loading clients: {str(e)}", fg='#F44336')
            messagebox.showerror("Error", f"Failed to load clients: {str(e)}")

    def on_create_clicked(self) -> None:
        """
        Handle Create Client button click with validation.

        Opens dialog for client name, validates input, creates client folder,
        and refreshes list.
        """
        # Get client name from user
        name = simpledialog.askstring(
            "Create Client",
            "Enter client name (letters, numbers, hyphens, underscores only):"
        )

        if name is None:  # User cancelled
            return

        # Sanitize input (strip whitespace)
        name = name.strip()

        if not name:
            messagebox.showerror(
                "Invalid Name",
                "Client name cannot be empty or whitespace only."
            )
            return

        # Validate and create client
        try:
            client_mgr = self.parent.get_client_manager()
            validated_name = client_mgr.validate_client_name(name)

            # Confirm if name was changed by validation
            if validated_name != name:
                messagebox.showwarning(
                    "Name Modified",
                    f"Client name modified during validation.\n"
                    f"Original: '{name}'\nValidated: '{validated_name}'"
                )

            # Create client
            client_mgr.create_client(validated_name, self.parent.project_root)

            self.refresh_list()
            messagebox.showinfo(
                "Success",
                f"Client '{validated_name}' created successfully."
            )

            # Update status
            self.status_label.config(
                text=f"Client '{validated_name}' created",
                fg='#4CAF50'
            )

        except ValueError as e:
            messagebox.showerror("Invalid Client Name", str(e))
            self.status_label.config(text="Create failed", fg='#F44336')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create client: {e}")
            self.status_label.config(text=f"Create failed: {str(e)}", fg='#F44336')

    def on_select_clicked(self) -> None:
        """
        Handle Select Client button click.

        Gets selected client from listbox, sets parent.selected_client,
        and navigates to MainMenuForm.
        """
        # Get selected index
        selection = self.client_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a client first")
            return

        # Get client name at selected index
        selected_index = selection[0]
        client_name = self.client_listbox.get(selected_index)

        # Set selected client in parent app
        self.parent.selected_client = client_name

        # Navigate to main menu
        from .main_menu_form import MainMenuForm
        self.parent.show_form(MainMenuForm)

    def on_delete_clicked(self) -> None:
        """
        Handle Delete Client button click.

        Shows confirmation dialog, validates selection, deletes client folder,
        and refreshes list.
        """
        # Get selected index
        selection = self.client_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a client to delete")
            return

        # Get client name at selected index
        selected_index = selection[0]
        client_name = self.client_listbox.get(selected_index)

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete client '{client_name}'?\n\n"
            f"This will permanently delete the client folder and all its contents."
        )
        if not confirm:
            return

        # Delete client
        try:
            client_mgr = self.parent.get_client_manager()
            client_mgr.delete_client(client_name, self.parent.project_root)

            self.refresh_list()

            # Update status
            self.status_label.config(
                text=f"Client '{client_name}' deleted",
                fg='#4CAF50'
            )

            messagebox.showinfo(
                "Success",
                f"Client '{client_name}' deleted successfully."
            )

        except ValueError as e:
            messagebox.showerror("Error", str(e))
            self.status_label.config(text="Delete failed", fg='#F44336')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete client: {e}")
            self.status_label.config(text=f"Delete failed: {str(e)}", fg='#F44336')

    def on_exit_clicked(self) -> None:
        """
        Handle Exit button click - quit application.
        """
        self.parent.quit()
