import tkinter as tk
from tkinter import messagebox

class TicTacToe:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic-Tac-Toe")
        self.current_player = "X"
        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.buttons = {}
        self.create_gui()
        
    def create_gui(self):
        """Create the 3x3 grid and control buttons."""
        self.root.geometry("300x350")
        self.grid_frame = tk.Frame(self.root)
        self.grid_frame.pack(pady=10)
        
        # Create 3x3 grid of buttons
        for i in range(3):
            for j in range(3):
                btn = tk.Button(
                    self.grid_frame, text="", font=("Arial", 24), width=5, height=2,
                    command=lambda r=i, c=j: self.make_move(r, c)
                )
                btn.grid(row=i, column=j, padx=2, pady=2)
                self.buttons[(i, j)] = btn
        
        # Status label
        self.status_var = tk.StringVar(value="X's turn")
        tk.Label(self.root, textvariable=self.status_var, font=("Arial", 14)).pack(pady=5)
        
        # New game button
        tk.Button(self.root, text="New Game", font=("Arial", 12), command=self.reset_game).pack(pady=5)
    
    def make_move(self, row, col):
        """Handle a player's move."""
        if self.board[row][col] == "" and not self.check_winner():
            self.board[row][col] = self.current_player
            self.buttons[(row, col)].config(text=self.current_player, bg="lightblue" if self.current_player == "X" else "lightgreen")
            
            if self.check_winner():
                self.status_var.set(f"{self.current_player} wins!")
                messagebox.showinfo("Tic-Tac-Toe", f"{self.current_player} wins!")
                self.highlight_winner()
            elif self.is_board_full():
                self.status_var.set("Draw!")
                messagebox.showinfo("Tic-Tac-Toe", "It's a draw!")
            else:
                self.current_player = "O" if self.current_player == "X" else "X"
                self.status_var.set(f"{self.current_player}'s turn")
    
    def check_winner(self):
        """Check for a winner."""
        # Check rows
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != "":
                return True
        # Check columns
        for j in range(3):
            if self.board[0][j] == self.board[1][j] == self.board[2][j] != "":
                return True
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != "":
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != "":
            return True
        return False
    
    def highlight_winner(self):
        """Highlight the winning line."""
        # Highlight rows
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != "":
                for j in range(3):
                    self.buttons[(i, j)].config(bg="yellow")
                return
        # Highlight columns
        for j in range(3):
            if self.board[0][j] == self.board[1][j] == self.board[2][j] != "":
                for i in range(3):
                    self.buttons[(i, j)].config(bg="yellow")
                return
        # Highlight diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != "":
            for i in range(3):
                self.buttons[(i, i)].config(bg="yellow")
            return
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != "":
            for i in range(3):
                self.buttons[(i, 2-i)].config(bg="yellow")
    
    def is_board_full(self):
        """Check if the board is full."""
        return all(self.board[i][j] != "" for i in range(3) for j in range(3))
    
    def reset_game(self):
        """Start a new game."""
        self.current_player = "X"
        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.status_var.set("X's turn")
        for i in range(3):
            for j in range(3):
                self.buttons[(i, j)].config(text="", bg="SystemButtonFace")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        game = TicTacToe(root)
        root.mainloop()
    except ImportError as e:
        print("Error: Tkinter is not installed or not working. Please ensure you have Tkinter available.")
        print("On Windows/Linux, Tkinter is included with Python. On Linux, you may need to install python3-tk (e.g., sudo apt-get install python3-tk).")
        print(f"Detailed error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")