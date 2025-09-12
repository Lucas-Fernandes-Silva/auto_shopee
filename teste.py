class Pessoa:
    def __init__(self, nome, idade):
        self.nome = nome
        self.idade = idade

    def apresentar(self):
        print(f'Olá meu nome é {self.nome} e tenho {self.idade}Anos')
        

p1 = Pessoa('Ana', 25)
p2 = Pessoa('Maria', 23)



class Funcionario(Pessoa):
    def __init__(self, nome, idade,salario):
        super().__init__(nome, idade)
        self.salario = salario

    def trabalhar(self):
        message = (f'{self.nome} está trabalhando')
        return message

    def aumentar_salario(self, valor):
        self.salario += valor
        return self.salario
    
f1 = Funcionario('Lucas', 25, 200.00)



print(f'{f1.nome}, \n {f1.trabalhar()},\n {f1.aumentar_salario(200)}')