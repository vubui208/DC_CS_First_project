import tkinter as tk
from tkinter import messagebox
from tkinter import ttk


tax_rate = 0.08  #8% tax

screen_bg     = "#1f2937"
PANEL_MENU_BG = "#374151"
PANEL_QTY_BG  = "#4b5563"
PANEL_CART_BG = "#6b7280"
CARD_BG       = "#374151"
CARD_BORDER   = "#4b5563"
TITLE_FG      = "#f3f4f6"
ACCENT        = "#9ca3af"
BTN_FG        = "#111827"


COUPONS = {
    "SAVE10":  ("percent", 10),  
    "OFF5":    ("amount",  5),   
    "STUDENT": ("percent", 15),
}

#temp data
MENU = {
    "Starters": {
        "Spring Rolls":    {"price": 5.50, "stock": 12},
        "Garlic Bread":    {"price": 4.25, "stock": 10},
        "Tomato Soup":     {"price": 4.75, "stock": 8},   
    },
    "Mains": {
        "Grilled Chicken": {"price": 12.99, "stock": 10},
        "Beef Burger":     {"price": 11.50, "stock": 9},
        "Veggie Pasta":    {"price": 10.75, "stock": 7},
    },
    "Drinks": {
        "Iced Tea":        {"price": 2.99, "stock": 20},
        "Lemonade":        {"price": 3.25, "stock": 16},
        "Sparkling Water": {"price": 2.50, "stock": 18},
    },
    "Desserts": {
        "Cheesecake":          {"price": 6.25, "stock": 8},
        "Chocolate Lava Cake": {"price": 6.99, "stock": 6},
        "Ice Cream Scoop":     {"price": 3.75, "stock": 15},
    },
}

# ================== Selected state ==================
selected = {"frame": None}

def select_frame(frame: tk.Frame):
    # if other is already selected
    if selected["frame"] is not None and selected["frame"] != frame:
        selected["frame"].configure(highlightbackground=CARD_BORDER, highlightthickness=1, bg=CARD_BG)
    selected["frame"] = frame
    frame.configure(highlightbackground="#000080", highlightthickness=2, bg=CARD_BG)

def clear_selected():
    if selected["frame"] is not None:
        selected["frame"].configure(highlightbackground=CARD_BORDER, highlightthickness=1, bg=CARD_BG)
    selected["frame"] = None

#state
cart_items = [] 
active_coupon = None  

def des(item_name, price, qty):
    return {"item_name": item_name, "price": price, "qty": qty}

def to_add_items(main, item_name, price, stock):
    #create frame + selected area
    item_frame = tk.Frame(main, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1, bd=0)
    item_frame.pack(fill="x", padx=5, pady=2)
    item_frame.bind("<Button-1>", lambda e, f=item_frame: select_frame(f))

    name_label = tk.Label(item_frame, text=item_name, bg=CARD_BG, fg="black", font=("Segoe UI", 12))
    name_label.pack(fill="x", padx=5, pady=2)
    name_label.bind("<Button-1>", lambda e, f=item_frame: select_frame(f))

    price_label = tk.Label(item_frame, text=f"${price:.2f}", bg=CARD_BG, fg=ACCENT, font=("Segoe UI", 12))
    price_label.pack(fill="x", padx=5, pady=1)
    price_label.bind("<Button-1>", lambda e, f=item_frame: select_frame(f))

    stock_label = tk.Label(item_frame, text=f"Stock: {stock}", bg=CARD_BG, fg="black", font=("Segoe UI", 10))
    stock_label.pack(fill="x", padx=5, pady=1)
    stock_label.bind("<Button-1>", lambda e, f=item_frame: select_frame(f))

    add_cart_button = ttk.Button(item_frame, text="Add to cart", style="Flat.TButton", takefocus=0,
                                 command=lambda f=item_frame: handleAddButton(f, item_name, price))
    add_cart_button.pack(fill="x", padx=10, pady=5)
def apply_coupon():
    global active_coupon
    code = coupon_var.get().strip().upper()
    if code in COUPONS:
        active_coupon = COUPONS[code]
        kind, val = active_coupon
        coupon_msg.set(f"Applied: {val}% off" if kind=="percent" else f"Applied: -${val:.2f}")
    else:
        active_coupon = None
        coupon_msg.set("Invalid code")
    update_totals()


def compute_subtotal():
    res = 0 
    for item in cart_items:
        res += item["price"] * item["qty"]
    return res

def compute_discount(subtotal):
    if not active_coupon:
        return 0.0
    kind, val = active_coupon
    return subtotal * (val/100) if kind == "percent" else min(val, subtotal)

def update_totals():
    subtotal = compute_subtotal()
    discount = compute_discount(subtotal)
    taxable  = subtotal - discount
    tax_amt  = taxable * tax_rate
    total    = taxable + tax_amt

    subtotal_var.set(f"Subtotal: ${subtotal:.2f}")
    discount_var.set(f"Discount: -${discount:.2f}")
    tax_var.set(f"Tax ({round(tax_rate*100,2)}%): ${tax_amt:.2f}")
    total_var.set(f"Total: ${total:.2f}")

def clear_cart():
    if cart_items:
    #return stock
        for item in cart_items:
            item_name = item["item_name"]
            qty = item["qty"]
            
            for category in MENU.values():
                if item_name in category:
                    category[item_name]["stock"] += qty
                    break
        
        #remove and re print all the thing to update stock
        selected["frame"] = None
        for notebook_frame in [starter, mains, drinks, desserts]:
            for widget in notebook_frame.winfo_children():
                widget.destroy()
        for name, data in MENU["Starters"].items():  
            to_add_items(starter, name, data["price"], data["stock"])
        for name, data in MENU["Mains"].items():     
            to_add_items(mains, name, data["price"], data["stock"])
        for name, data in MENU["Drinks"].items():    
            to_add_items(drinks, name, data["price"], data["stock"])
        for name, data in MENU["Desserts"].items():  
            to_add_items(desserts, name, data["price"], data["stock"])
        
        #remove cart
        for w in cart_card.winfo_children():
            w.destroy()
        cart_card.pack_forget()
        cart_items.clear()
        update_totals()
        clear_selected()
    else:
        messagebox.showinfo("Empty Cart", "Your cart is empty.")
def format_receipt_text():
    lines = []
    lines.append("===== RECEIPT =====")
    lines.append("")
    if not cart_items:
        lines.append("No items.")
        return "\n".join(lines)
    # Items
    for item in cart_items:
        name = item["item_name"]
        qty = item["qty"]
        price = item["price"]
        line_total = price * qty
        lines.append(f"{name} x{qty} @ ${price:.2f} = ${line_total:.2f}")
    lines.append("")
    # Totals
    subtotal = compute_subtotal()
    discount = compute_discount(subtotal)
    taxable = subtotal - discount
    tax_amt = taxable * tax_rate
    total = taxable + tax_amt
    if active_coupon:
        kind, val = active_coupon
        coupon_str = f"Coupon: {'%d%%' % val if kind=='percent' else '$%.2f' % val}"
        lines.append(coupon_str)
    lines.append(f"Subtotal: ${subtotal:.2f}")
    lines.append(f"Discount: -${discount:.2f}")
    lines.append(f"Tax ({round(tax_rate*100,2)}%): ${tax_amt:.2f}")
    lines.append(f"TOTAL: ${total:.2f}")
    lines.append("===================")
    return "\n".join(lines)

def check_out():
    if not cart_items:
        messagebox.showinfo("Empty Cart", "Your cart is empty.")
        return
    receipt_win = tk.Toplevel(screen)
    receipt_win.title("Receipt")
    receipt_win.geometry("400x500")
    receipt_win.configure(bg=CARD_BG)

    text = tk.Text(receipt_win, bg=CARD_BG, fg=TITLE_FG, font=("Segoe UI", 11), wrap="word", borderwidth=0)
    text.pack(fill="both", expand=True, padx=10, pady=10)
    text.insert("1.0", format_receipt_text())
    text.configure(state="disabled")

    btn_row = tk.Frame(receipt_win, bg=CARD_BG)
    btn_row.pack(fill="x", padx=10, pady=(0,10))

    def confirm_and_close():
        clear_cart()
        receipt_win.destroy()

    ttk.Button(btn_row, text="Confirm", command=confirm_and_close).pack(side="right")
    ttk.Button(btn_row, text="Close", command=receipt_win.destroy).pack(side="right", padx=(0,8))
def handleAddButton(item_frame, item_name, price):
    #only add if selected

    if selected["frame"] is None or selected["frame"] != item_frame:
        messagebox.showinfo("Select item", "Click on it before adding to cart.")
        return
    qty = int(qty_entry.get().strip())
    if qty <= 0:
        #if neg then return 1
        qty_entry.delete(0, tk.END)  
        qty_entry.insert(0, "1")     
        messagebox.showerror("Invalid Quantity", "Quantity must be greater than 0.")
        return
    #get data
    item_data = None
    for category in MENU.values():
        if item_name in category:
            item_data = category[item_name]
            break
    #if it is enough to buy
    if item_data["stock"] < qty:
        messagebox.showerror("Out of Stock", f"Only {item_data['stock']} items available!")
        return
    item_data["stock"] -= qty
    
    #change the stock
    for widget in item_frame.winfo_children():
        if isinstance(widget, tk.Label) and widget.cget("text").startswith("Stock:"):
            widget.configure(text=f"Stock: {item_data['stock']}")
            break

    #show cart if it is hidden
    if not cart_card.winfo_ismapped():
        cart_card.pack(padx=10, pady=10, fill="x", before=totals_card)

    #add items to cart
    cart_items.append(des(item_name, price, qty))

    #print in cart
    row = tk.Frame(cart_card, bg=CARD_BG); row.pack(fill="x", padx=6, pady=4)
    tk.Label(row, text=f"{item_name}  x{qty}", bg=CARD_BG, fg="black", font=("Segoe UI", 12)).pack(side="left")
    tk.Label(row, text=f"${price*qty:.2f}", bg=CARD_BG, fg=ACCENT, font=("Segoe UI", 12)).pack(side="right")
    update_totals()
    clear_selected() #remove selected state after add

#create window
screen = tk.Tk()
screen.title("Vu sigma")
screen.geometry("1000x500")
screen.configure(bg="#A9A9A9")

#style
style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background=screen_bg, foreground="black", font=("Arial", 12))
style.configure("TEntry", background="#3b3b3b", foreground="black", font=("Arial", 12))
style.configure("TButton", background="#A9A9A9", foreground="black", font=("Arial", 12))


main_frame = tk.Frame(screen, bg=screen_bg)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

#split into 3 frames
main_frame.rowconfigure(0, weight=1)
main_frame.columnconfigure(0, weight=1, uniform="group1")
main_frame.columnconfigure(1, weight=1, uniform="group1")
main_frame.columnconfigure(2, weight=2, uniform="group1")

#menu
menu_outer = tk.Frame(main_frame, bg=PANEL_MENU_BG, bd=0)
menu_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

menu_title = tk.Label(menu_outer, text="Menu", bg=PANEL_MENU_BG, fg=TITLE_FG, font=("Segoe UI", 14, "bold"))
menu_title.pack(anchor="w", padx=10, pady=(8, 4))
notebook_main = ttk.Notebook(menu_outer)
notebook_main.pack(expand=True, fill="both", padx=6, pady=6)

starter = tk.Frame(notebook_main, bg=PANEL_MENU_BG, bd=0);  notebook_main.add(starter,  text="Starters")
mains   = tk.Frame(notebook_main, bg=PANEL_MENU_BG, bd=0);  notebook_main.add(mains,    text="Mains")
drinks  = tk.Frame(notebook_main, bg=PANEL_MENU_BG, bd=0);  notebook_main.add(drinks,   text="Drinks")
desserts= tk.Frame(notebook_main, bg=PANEL_MENU_BG, bd=0);  notebook_main.add(desserts, text="Desserts")

#display item

for name, data in MENU["Starters"].items():  
    to_add_items(starter,  name, data["price"], data["stock"])
for name, data in MENU["Mains"].items():     
    to_add_items(mains,    name, data["price"], data["stock"])
for name, data in MENU["Drinks"].items():    
    to_add_items(drinks,   name, data["price"], data["stock"])
for name, data in MENU["Desserts"].items():  
    to_add_items(desserts, name, data["price"], data["stock"])

#second frame
qty_outer = tk.Frame(main_frame, bg=PANEL_QTY_BG, bd=0)
qty_outer.grid(row=0, column=1, sticky="nsew", padx=(0, 8))

qty_title = tk.Label(qty_outer, text="Quantity", bg=PANEL_QTY_BG, fg=TITLE_FG, font=("Segoe UI", 14, "bold"))
qty_title.pack(anchor="w", padx=10, pady=(8, 4))

qty_card = tk.Frame(qty_outer, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1, bd=0)
qty_card.pack(padx=10, pady=10, fill="x")

qty_label = tk.Label(qty_card, text="Enter Quantity", bg=CARD_BG, fg="black", font=("Segoe UI", 12))
qty_label.pack(anchor="w", padx=10, pady=(8, 4))

qty_entry = ttk.Entry(qty_card, font=("Segoe UI", 12), width=8, justify="center")
qty_entry.pack(padx=10, pady=10, fill="x")
qty_entry.insert(0, "1")



#third frame
cart_outer = tk.Frame(main_frame, bg=PANEL_CART_BG, bd=0)
cart_outer.grid(row=0, column=2, sticky="nsew")

cart_title = tk.Label(cart_outer, text="Cart", bg=PANEL_CART_BG, fg=TITLE_FG, font=("Segoe UI", 14, "bold"))
cart_title.pack(anchor="w", padx=10, pady=(8, 4))

#this is container only / show when there is item
cart_card = tk.Frame(cart_outer, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1, bd=0)

#place to cal the price
totals_card = tk.Frame(cart_outer, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1, bd=0)
totals_card.pack(padx=10, pady=(0,10), fill="x")

subtotal_var = tk.StringVar(value="Subtotal: $0.00")
discount_var = tk.StringVar(value="Discount: -$0.00")
tax_var      = tk.StringVar(value=f"Tax ({round(tax_rate*100,2)}%): $0.00")
total_var    = tk.StringVar(value="Total: $0.00")

tk.Label(totals_card, textvariable=subtotal_var, bg=CARD_BG, fg=TITLE_FG).pack(anchor="w", padx=10, pady=(8,0))
tk.Label(totals_card, textvariable=discount_var, bg=CARD_BG, fg="#fecaca").pack(anchor="w", padx=10)
tk.Label(totals_card, textvariable=tax_var,      bg=CARD_BG, fg=TITLE_FG).pack(anchor="w", padx=10)
tk.Label(totals_card, textvariable=total_var,    bg=CARD_BG, fg=TITLE_FG, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(0,8))

coupon_row = tk.Frame(totals_card, bg=CARD_BG)
coupon_row.pack(fill="x", padx=10, pady=(0,8))
coupon_var = tk.StringVar()
coupon_msg = tk.StringVar(value="")
ttk.Entry(coupon_row, textvariable=coupon_var, width=16).pack(side="left")
tk.Label(coupon_row, textvariable=coupon_msg, bg=CARD_BG, fg="#86efac").pack(side="left", padx=8)
ttk.Button(coupon_row, text="Apply", command=apply_coupon).pack(side="right")


bottom_bar = tk.Frame(cart_outer, bg=PANEL_CART_BG)
bottom_bar.pack(side="bottom", fill="x", padx=10, pady=(0,10))

check_out_btn = ttk.Button(bottom_bar, text="Check Out", command=check_out)
check_out_btn.pack(side="left")

clear_btn = ttk.Button(bottom_bar, text="Clear Cart", command=clear_cart)
clear_btn.pack(side="right")


screen.mainloop()
