def add(a,b):
    return a+b
def subtract(a,b):
    return a-b
def multiply(a,b):
    return a*b

session =[]

user = "y"
while(user == 'y'):
    a = int(input("enter number 1: "))
    b = int(input("enter number 2: "))
    sign = input("enter the sign: ").strip()
    if sign == "+":
        print(add(a,b))
        session.append([a,b,"+",add(a,b)])
    elif sign == "-":
        print(subtract(a,b))
        session.append([a,b,"-",subtract(a,b)])
    elif sign == "x":
        print(multiply(a,b))
        session.append([a,b,"x",multiply(a,b)])
    elif sign == "/":
        print(multiply(a,1/b))
        session.append([a,b,"/",multiply(a,1/b)])
    user = input("Do you want to continue? Y/N").lower()
for i in range(0,len(session)):
    print(f"section {i} : {session[i]}")