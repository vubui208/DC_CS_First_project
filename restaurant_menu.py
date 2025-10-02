import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import json
import os
from datetime import datetime

tax_rate = 0.08  #8% tax
active_coupon = False
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

# User management
USERS_FILE = "users.json"
RECEIPTS_DIR = "receipts"
# Base menu file used before login or for guests
MENU_FILE = "menu.json"

#default account
DEFAULT_USERS = {
    "admin": {"password": "admin123", "role": "admin"},
}

current_user = None

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_USERS.copy()

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def ensure_receipts_path():
    if not os.path.exists(RECEIPTS_DIR):
        os.makedirs(RECEIPTS_DIR, exist_ok=True)

DEFAULT_MENU = {
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

def get_menu_file_for_user():
    # Each admin gets their own menu file; guests/customers use the shared default
    if current_user and current_user.get("role") == "admin":
        username = current_user.get("username", "admin")
        return f"menu_{username}.json"
    return MENU_FILE

def load_menu():
    menu_path = get_menu_file_for_user()
    if os.path.exists(menu_path):
        with open(menu_path, 'r') as f:
            return json.load(f)
    # If missing: create from defaults and save to disk
    menu_obj = DEFAULT_MENU.copy()
    with open(menu_path, 'w') as f:
        json.dump(menu_obj, f, indent=2)
    return menu_obj

def save_menu(menu_obj):
    menu_path = get_menu_file_for_user()
    with open(menu_path, 'w') as f:
        json.dump(menu_obj, f, indent=2)

MENU = load_menu()
cart_items =[]
selected = {"frame": None}

def select_frame(frame: tk.Frame):
    if selected["frame"] is not None and selected["frame"] != frame:
        selected["frame"].configure(highlightbackground=CARD_BORDER, highlightthickness=1, bg=CARD_BG)
    selected["frame"] = frame
    frame.configure(highlightbackground="#000080", highlightthickness=2, bg=CARD_BG)

def clear_selected():
    if selected["frame"] is not None:
        selected["frame"].configure(highlightbackground=CARD_BORDER, highlightthickness=1, bg=CARD_BG)
    selected["frame"] = None

def make_scrollable(parent: tk.Widget, bg_color: str) -> tk.Frame:
  
    STEP_PER_TICK = 0.07    
    FRICTION      = 0.88    
    FRAME_MS      = 12      

    container = tk.Frame(parent, bg=bg_color)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0, bg=bg_color)
    vbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    vbar.pack(side="right", fill="y")

    inner = tk.Frame(canvas, bg=bg_color)
    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def on_inner_config(_):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfigure(window_id, width=canvas.winfo_width())

    inner.bind("<Configure>", on_inner_config)
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))

    
    state = {"velocity": 0.0, "animating": False, "job": None}

    def clamp01(x): 
        return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

    def current_pos():
       
        return canvas.yview()[0] if canvas.yview() else 0.0

    def animate():
        
        pos = current_pos()
        pos += state["velocity"]
        pos = clamp01(pos)
        canvas.yview_moveto(pos)

        state["velocity"] *= FRICTION
        if abs(state["velocity"]) < 0.001:
            state["velocity"] = 0.0
            state["animating"] = False
            state["job"] = None
            return

        state["job"] = canvas.after(FRAME_MS, animate)

    def kick():
        if not state["animating"]:
            state["animating"] = True
            animate()

    # ===== Wheel handler (Win/mac trackpad) =====
    def on_wheel(event):
        
        scale = (event.delta / 120.0) if getattr(event, "delta", 0) else 0
       
        state["velocity"] += -scale * STEP_PER_TICK
        kick()

    # ===== Linux buttons =====
    def on_btn4(_):  # up
        state["velocity"] += -STEP_PER_TICK
        kick()

    def on_btn5(_):  # down
        state["velocity"] += STEP_PER_TICK
        kick()

    
    def bind_all(_=None):
        canvas.bind_all("<MouseWheel>", on_wheel)  # Win/mac
        canvas.bind_all("<Button-4>", on_btn4)     # Linux up
        canvas.bind_all("<Button-5>", on_btn5)     # Linux down

    def unbind_all(_=None):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    for w in (canvas, inner):
        w.bind("<Enter>", bind_all)
        w.bind("<Leave>", unbind_all)

    return inner


def des(item_name, price, qty):
    return {"item_name": item_name, "price": price, "qty": qty}

def to_add_items(main, item_name, price, stock):
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

def refresh_menu_items():
    for notebook_frame in [starter, mains, drinks, desserts]:
        for widget in notebook_frame.winfo_children():
            widget.destroy()
    for name, data in MENU.get("Starters", {}).items():  
        to_add_items(starter, name, data["price"], data["stock"])
    for name, data in MENU.get("Mains", {}).items():     
        to_add_items(mains, name, data["price"], data["stock"])
    for name, data in MENU.get("Drinks", {}).items():    
        to_add_items(drinks, name, data["price"], data["stock"])
    for name, data in MENU.get("Desserts", {}).items():  
        to_add_items(desserts, name, data["price"], data["stock"])

def clear_cart():
    if cart_items:
        for item in cart_items:
            item_name = item["item_name"]
            qty = item["qty"]
            for category in MENU.values():
                if item_name in category:
                    category[item_name]["stock"] += qty
                    break
        selected["frame"] = None
        refresh_menu_items()
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
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if current_user:
        lines.append(f"Customer: {current_user['username']}")
    lines.append("")
    if not cart_items:
        lines.append("No items.")
        return "\n".join(lines)
    for item in cart_items:
        name = item["item_name"]
        qty = item["qty"]
        price = item["price"]
        line_total = price * qty
        lines.append(f"{name} x{qty} @ ${price:.2f} = ${line_total:.2f}")
    lines.append("")
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

def save_receipt_to_file():
    ensure_receipts_path()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    username = current_user['username'] if current_user else 'guest'
    filename = os.path.join(RECEIPTS_DIR, f"receipt_{username}_{timestamp}.txt")
    with open(filename, 'w') as f:
        f.write(format_receipt_text())
    return filename

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
        receipt_file = save_receipt_to_file()
        messagebox.showinfo("Receipt Saved", f"Receipt saved to: {receipt_file}")
        selected["frame"] = None
        refresh_menu_items()
        for w in cart_card.winfo_children():
            w.destroy()
        cart_card.pack_forget()
        cart_items.clear()
        update_totals()
        clear_selected()
        receipt_win.destroy()

    ttk.Button(btn_row, text="Confirm", command=confirm_and_close).pack(side="right")
    ttk.Button(btn_row, text="Close", command=receipt_win.destroy).pack(side="right", padx=(0,8))

def handleAddButton(item_frame, item_name, price):
    if selected["frame"] is None or selected["frame"] != item_frame:
        messagebox.showinfo("Select item", "Click on it before adding to cart.")
        return
    qty = int(qty_entry.get().strip())
    if qty <= 0:
        qty_entry.delete(0, tk.END)  
        qty_entry.insert(0, "1")     
        messagebox.showerror("Invalid Quantity", "Quantity must be greater than 0.")
        return
    item_data = None
    for category in MENU.values():
        if item_name in category:
            item_data = category[item_name]
            break
    if item_data["stock"] < qty:
        messagebox.showerror("Out of Stock", f"Only {item_data['stock']} items available!")
        return
    item_data["stock"] -= qty
    for widget in item_frame.winfo_children():
        if isinstance(widget, tk.Label) and widget.cget("text").startswith("Stock:"):
            widget.configure(text=f"Stock: {item_data['stock']}")
            break
    if not cart_card.winfo_ismapped():
        cart_card.pack(padx=10, pady=10, fill="x", before=totals_card)
    cart_items.append(des(item_name, price, qty))
    row = tk.Frame(cart_card, bg=CARD_BG); row.pack(fill="x", padx=6, pady=4)
    tk.Label(row, text=f"{item_name}  x{qty}", bg=CARD_BG, fg="black", font=("Segoe UI", 12)).pack(side="left")
    tk.Label(row, text=f"${price*qty:.2f}", bg=CARD_BG, fg=ACCENT, font=("Segoe UI", 12)).pack(side="right")
    update_totals()
    clear_selected()

def build_admin_tab():
    admin_tab = tk.Frame(notebook_main, bg=PANEL_MENU_BG, bd=0)
    notebook_main.add(admin_tab, text="Admin")

    row = tk.Frame(admin_tab, bg=PANEL_MENU_BG); row.pack(fill="x", padx=10, pady=6)
    tk.Label(row, text="Category", bg=PANEL_MENU_BG, fg=TITLE_FG).pack(side="left")
    categories = list(MENU.keys()) + ["New..."]
    cat_var = tk.StringVar(value=categories[0])
    cat_combo = ttk.Combobox(row, textvariable=cat_var, values=categories, state="readonly", width=18)
    cat_combo.pack(side="left", padx=8)

    new_cat_row = tk.Frame(admin_tab, bg=PANEL_MENU_BG); 
    new_cat_label = tk.Label(new_cat_row, text="New Category Name", bg=PANEL_MENU_BG, fg=TITLE_FG)
    new_cat_label.pack(side="left")
    new_cat_var = tk.StringVar()
    new_cat_entry = ttk.Entry(new_cat_row, textvariable=new_cat_var, width=22)
    new_cat_entry.pack(side="left", padx=8)

    def on_cat_change(event=None):
        if cat_var.get()=="New...":
            new_cat_row.pack(fill="x", padx=10, pady=6)
        else:
            try:
                new_cat_row.forget()
            except:
                pass
    cat_combo.bind("<<ComboboxSelected>>", on_cat_change)

    row2 = tk.Frame(admin_tab, bg=PANEL_MENU_BG); row2.pack(fill="x", padx=10, pady=6)
    tk.Label(row2, text="Item", bg=PANEL_MENU_BG, fg=TITLE_FG).pack(side="left")
    item_var = tk.StringVar()
    ttk.Entry(row2, textvariable=item_var, width=22).pack(side="left", padx=8)

    row3 = tk.Frame(admin_tab, bg=PANEL_MENU_BG); row3.pack(fill="x", padx=10, pady=6)
    tk.Label(row3, text="Price", bg=PANEL_MENU_BG, fg=TITLE_FG).pack(side="left")
    price_var = tk.StringVar()
    ttk.Entry(row3, textvariable=price_var, width=10).pack(side="left", padx=8)
    tk.Label(row3, text="Stock", bg=PANEL_MENU_BG, fg=TITLE_FG).pack(side="left", padx=(12,0))
    stock_var = tk.StringVar()
    ttk.Entry(row3, textvariable=stock_var, width=10).pack(side="left", padx=8)

    def add_item():
        cat = cat_var.get()
        if cat == "New...":
            cat = new_cat_var.get().strip()
            if not cat:
                messagebox.showerror("Error", "Enter new category name.")
                return
            if cat not in MENU:
                MENU[cat] = {}
        name = item_var.get().strip()
        try:
            price = float(price_var.get().strip())
            stock = int(stock_var.get().strip())
        except:
            messagebox.showerror("Error", "Invalid price/stock.")
            return
        if not name:
            messagebox.showerror("Error", "Item name required.")
            return
        MENU.setdefault(cat, {})
        MENU[cat][name] = {"price": price, "stock": stock}
        save_menu(MENU)
        refresh_menu_items()
        messagebox.showinfo("Added", f"Added {name} to {cat}.")
        item_var.set(""); price_var.set(""); stock_var.set("")

    ttk.Button(admin_tab, text="Add Item", command=add_item).pack(padx=10, pady=10, anchor="w")

def build_main_ui():
    global notebook_main, starter, mains, drinks, desserts
    global qty_entry, cart_card, totals_card, subtotal_var, discount_var, tax_var, total_var
    global coupon_var, coupon_msg

    menu_title = tk.Label(menu_outer, text="Menu", bg=PANEL_MENU_BG, fg=TITLE_FG, font=("Segoe UI", 14, "bold"))
    menu_title.pack(anchor="w", padx=10, pady=(8, 4))
    notebook_main = ttk.Notebook(menu_outer)
    notebook_main.pack(expand=True, fill="both", padx=6, pady=6)

    starter_tab = tk.Frame(notebook_main, bg=PANEL_MENU_BG, bd=0);  notebook_main.add(starter_tab,  text="Starters")
    mains_tab   = tk.Frame(notebook_main, bg=PANEL_MENU_BG, bd=0);  notebook_main.add(mains_tab,    text="Mains")
    drinks_tab  = tk.Frame(notebook_main, bg=PANEL_MENU_BG, bd=0);  notebook_main.add(drinks_tab,   text="Drinks")
    desserts_tab= tk.Frame(notebook_main, bg=PANEL_MENU_BG, bd=0);  notebook_main.add(desserts_tab, text="Desserts")

    # scrollable inner frames
    starter = make_scrollable(starter_tab, PANEL_MENU_BG)
    mains   = make_scrollable(mains_tab,   PANEL_MENU_BG)
    drinks  = make_scrollable(drinks_tab,  PANEL_MENU_BG)
    desserts= make_scrollable(desserts_tab,PANEL_MENU_BG)

    for name, data in MENU.get("Starters", {}).items():  
        to_add_items(starter,  name, data["price"], data["stock"])
    for name, data in MENU.get("Mains", {}).items():     
        to_add_items(mains,    name, data["price"], data["stock"])
    for name, data in MENU.get("Drinks", {}).items():    
        to_add_items(drinks,   name, data["price"], data["stock"])
    for name, data in MENU.get("Desserts", {}).items():  
        to_add_items(desserts, name, data["price"], data["stock"])

    if current_user and current_user.get("role") == "admin":
        build_admin_tab()

    qty_title = tk.Label(qty_outer, text="Quantity", bg=PANEL_QTY_BG, fg=TITLE_FG, font=("Segoe UI", 14, "bold"))
    qty_title.pack(anchor="w", padx=10, pady=(8, 4))

    qty_card = tk.Frame(qty_outer, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1, bd=0)
    qty_card.pack(padx=10, pady=10, fill="x")

    qty_label = tk.Label(qty_card, text="Enter Quantity", bg=CARD_BG, fg="black", font=("Segoe UI", 12))
    qty_label.pack(anchor="w", padx=10, pady=(8, 4))

    qty_entry = ttk.Entry(qty_card, font=("Segoe UI", 12), width=8, justify="center")
    qty_entry.pack(padx=10, pady=10, fill="x")
    qty_entry.insert(0, "1")

    cart_title = tk.Label(cart_outer, text="Cart", bg=PANEL_CART_BG, fg=TITLE_FG, font=("Segoe UI", 14, "bold"))
    cart_title.pack(anchor="w", padx=10, pady=(8, 4))

    cart_card = tk.Frame(cart_outer, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1, bd=0)

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

def do_login_register_ui():
    login_win = tk.Toplevel(screen)
    login_win.title("Admin Login / Register")
    login_win.geometry("360x260")
    login_win.configure(bg=CARD_BG)
    login_win.grab_set()

    users = load_users()

    frm = tk.Frame(login_win, bg=CARD_BG); frm.pack(expand=True, fill="both", padx=16, pady=16)

    tk.Label(frm, text="Username (admin)", bg=CARD_BG, fg=TITLE_FG).pack(anchor="w")
    u_var = tk.StringVar(); ttk.Entry(frm, textvariable=u_var).pack(fill="x", pady=6)

    tk.Label(frm, text="Password", bg=CARD_BG, fg=TITLE_FG).pack(anchor="w")
    p_var = tk.StringVar(); ttk.Entry(frm, textvariable=p_var, show="*").pack(fill="x", pady=6)

    btns = tk.Frame(frm, bg=CARD_BG); btns.pack(fill="x", pady=10)

    def do_login():
        global current_user
        u = u_var.get().strip()
        p = p_var.get().strip()
        if u in users and users[u]["password"] == p and users[u]["role"] == "admin":
            current_user = {"username": u, "role": "admin"}
            login_win.destroy()
            # reload menu for this admin and rebuild UI
            globals()["MENU"] = load_menu()
            build_main_ui()
        else:
            messagebox.showerror("Login failed", "Admin only.")

    def do_register():
        u = u_var.get().strip()
        p = p_var.get().strip()
        if not u or not p:
            messagebox.showerror("Error", "Enter username and password.")
            return
        if u in users:
            messagebox.showerror("Error", "Username already exists.")
            return
        users[u] = {"password": p, "role": "admin"}
        save_users(users)
        messagebox.showinfo("Registered", "Admin registered successfully. Please login.")

    def continue_guest():
        global current_user
        current_user = {"username": "guest", "role": "customer"}
        login_win.destroy()
        # load shared menu and build
        globals()["MENU"] = load_menu()
        build_main_ui()

    ttk.Button(btns, text="Login", command=do_login).pack(side="left", padx=4)
    ttk.Button(btns, text="Register", command=do_register).pack(side="left", padx=4)
    ttk.Button(btns, text="Continue as Guest", command=continue_guest).pack(side="right", padx=4)

screen = tk.Tk()
screen.title("Vu sigma")
screen.geometry("1200x500")
screen.configure(bg="#A9A9A9")

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background=screen_bg, foreground="black", font=("Arial", 12))
style.configure("TEntry", background="#3b3b3b", foreground="black", font=("Arial", 12))
style.configure("TButton", background="#A9A9A9", foreground="black", font=("Arial", 12))

main_frame = tk.Frame(screen, bg=screen_bg)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

main_frame.rowconfigure(0, weight=1)
main_frame.columnconfigure(0, weight=1, uniform="group1")
main_frame.columnconfigure(1, weight=1, uniform="group1")
main_frame.columnconfigure(2, weight=2, uniform="group1")

menu_outer = tk.Frame(main_frame, bg=PANEL_MENU_BG, bd=0)
menu_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

qty_outer = tk.Frame(main_frame, bg=PANEL_QTY_BG, bd=0)
qty_outer.grid(row=0, column=1, sticky="nsew", padx=(0, 8))

cart_outer = tk.Frame(main_frame, bg=PANEL_CART_BG, bd=0)
cart_outer.grid(row=0, column=2, sticky="nsew")

do_login_register_ui()
screen.mainloop()
