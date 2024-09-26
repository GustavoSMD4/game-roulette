import tkinter as tk
from tkinter import messagebox
import requests
import math

class RoletaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Roleta")

        # Campos de entrada para aposta
        self.tipo_label = tk.Label(root, text="Tipo de Aposta (color ou number):", font=("Arial", 16))
        self.tipo_label.pack()
        self.tipo_entry = tk.Entry(root, font=("Arial", 16))
        self.tipo_entry.pack()

        self.bet_label = tk.Label(root, text="Aposta (número ou cor):", font=("Arial", 16))
        self.bet_label.pack()
        self.bet_entry = tk.Entry(root, font=("Arial", 16))
        self.bet_entry.pack()

        self.amount_label = tk.Label(root, text="Valor da Aposta:", font=("Arial", 16))
        self.amount_label.pack()
        self.amount_entry = tk.Entry(root, font=("Arial", 16))
        self.amount_entry.pack()

        self.start_button = tk.Button(root, text="Girar", command=self.iniciar_aposta, font=("Arial", 16), width=10)
        self.start_button.pack()

        self.result_label = tk.Label(root, text="", font=("Arial", 20))
        self.result_label.pack()

        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")  # Aumenta a largura
        self.canvas.pack()

        self.roleta_segments = 37  # Incluindo o 0
        self.radius = 250  # Aumenta o raio da roleta

        # Números vermelhos e pretos
        self.numeros_vermelhos = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        self.numeros_pretos = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

    def iniciar_aposta(self):
        tipo = self.tipo_entry.get().strip().lower()
        bet = self.bet_entry.get().strip().lower()
        try:
            bet_amount = int(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Erro", "Insira um valor de aposta válido.")
            return

        if tipo not in ["color", "number"]:
            messagebox.showerror("Erro", "Tipo de aposta inválido. Use 'color' ou 'number'.")
            return
        
        if tipo == "number" and not bet.isdigit():
            messagebox.showerror("Erro", "Para tipo 'number', insira um número válido.")
            return
        
        if tipo == "color" and bet not in ["red", "black"]:
            messagebox.showerror("Erro", "Para tipo 'color', use 'red' ou 'black'.")
            return
        
        self.chamar_api(tipo, bet, bet_amount)

    def chamar_api(self, tipo, bet, bet_amount):
        try:
            url = f"https://gustavosmd4gamble.pythonanywhere.com/roulette?type={tipo}&bet={bet}&betAmount={bet_amount}"
            response = requests.get(url)
            data = response.json()
            resultado = data['result']
            self.result_label.config(text=f"Resultado: {resultado}")

            # Obter o número do resultado
            numero = int(resultado.split()[1]) if tipo == "number" else self.obter_numero_por_cor(data['result'])

            # Exibir a roleta e a linha no número correto
            self.canvas.delete("all")
            self.desenhar_roleta()  # Desenhar a roleta final

            # Calcula o ângulo para a linha amarela
            angulo_final = (360 / self.roleta_segments) * numero + (360 / self.roleta_segments) / 2

            # Desenha a linha amarela no número correto
            self.canvas.create_line(400, 300,  # Centro ajustado para o novo canvas
                                    400 + (self.radius + 20) * math.cos(math.radians(angulo_final)), 
                                    300 + (self.radius + 20) * math.sin(math.radians(angulo_final)), 
                                    fill="yellow", width=4)  # Linha apontando o resultado

            # Pausa para visualizar o resultado
            self.root.after(1000, lambda: self.exibir_retorno_api(data))

        except Exception as e:
            messagebox.showerror("Erro", "Não foi possível conectar à API.")

    def obter_numero_por_cor(self, resultado):
        numero = int(resultado.split()[1])
        if numero in self.numeros_vermelhos:
            return numero
        elif numero in self.numeros_pretos:
            return numero
        return 0  # Se for 0, retorna 0 (verde)

    def exibir_retorno_api(self, data):
        message = data.get('message', 'Resultado desconhecido')
        amount = data.get('amount', 0)
        self.result_label.config(text=f"{message}, Result: {data.get('result')}\nTotal: {amount:.2f}")

    def desenhar_roleta(self):
        for i in range(self.roleta_segments):  # 0 a 36
            angle = (360 / self.roleta_segments) * i
            color = "red" if i in self.numeros_vermelhos else "black" if i in self.numeros_pretos else "green"  # O 0 é verde
            
            # Desenha o segmento da roleta
            x1 = 400 + self.radius * math.cos(math.radians(angle))  # Ajustado para o novo centro
            y1 = 300 + self.radius * math.sin(math.radians(angle))  # Ajustado para o novo centro
            x2 = 400 + self.radius * math.cos(math.radians(angle + 360 / self.roleta_segments))
            y2 = 300 + self.radius * math.sin(math.radians(angle + 360 / self.roleta_segments))
            self.canvas.create_polygon(400, 300, x1, y1, x2, y2, fill=color, outline="white")
            
            # Adiciona o número na posição correta
            num_angle = angle + (360 / self.roleta_segments) / 2  # Para centralizar o número
            num_x = 400 + (self.radius - 30) * math.cos(math.radians(num_angle))
            num_y = 300 + (self.radius - 30) * math.sin(math.radians(num_angle))
            self.canvas.create_text(num_x, num_y, text=str(i), font=("Arial", 16), fill="white")

if __name__ == "__main__":
    root = tk.Tk()
    app = RoletaApp(root)
    root.mainloop()
