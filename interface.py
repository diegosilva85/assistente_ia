import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from openai import OpenAI
from dotenv import dotenv_values, load_dotenv

class JanelaPrincipal:
    def __init__(self):
        self.assistentes = {'-':'-'}
        self.assistente_id = ''
        self.id_assistente = ''
        self.arquivos = []
        self.row = 7
        self.janela_principal = tk.Tk()
        self.janela_principal.title("GPT-Assistente")
        tab_control = ttk.Notebook(self.janela_principal)
        self.tab1 = ttk.Frame(tab_control)
        self.tab2 = ttk.Frame(tab_control)
        tab_control.add(self.tab1, text='Criação de Assistente de IA')
        tab_control.add(self.tab2, text='Chat')
        tab_control.pack(expand=1, fill='both')

        # Aba 1 - Criar assistente IA
        criar_label = tk.Label(self.tab1, text="Criar um assistente de IA")
        criar_label.grid(row=0, column=0,columnspan=2, pady=5, padx=5)
        
        nome_label = tk.Label(self.tab1, text="Nome do Assistente")
        nome_label.grid(row=1, column=0, pady=5, padx=5)
        self.nome_entry = tk.Entry(self.tab1, width=35)
        self.nome_entry.grid(row=2, column=0, padx=5, pady=5)

        modelo_nome = tk.Label(self.tab1, text='Modelo GPT')
        modelo_nome.grid(row=3, column=0, padx=5, pady=5)
        opcoes_modelo = ['gpt-3.5-turbo', 'gpt-4.0']
        self.opcoes_var = tk.StringVar(self.tab1)
        self.opcoes_var.set(opcoes_modelo[0])
        valor_modelo = tk.OptionMenu(self.tab1, self.opcoes_var, *opcoes_modelo)
        valor_modelo.grid(row=4, column=0, padx=5, pady=5)

        api_label = tk.Label(self.tab1, text='API_KEY do Projeto')
        api_label.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        self.api_entry = tk.Entry(self.tab1, width=35)
        self.api_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5)
        botao_carregar_key = tk.Button(self.tab1, text='Carregar API Key do arquivo', command=self.carregar_api_key)
        botao_carregar_key.grid(row=3, column=1, padx=5, pady=5)

        instrucoes_label = tk.Label(self.tab1, text='Instruções para o assistente (Prompt Engineering)')
        instrucoes_label.grid(row=5, column=0, columnspan=3, padx=5, pady=5)
        self.instrucoes_texto = tk.Text(self.tab1, width=70, height=20)
        self.instrucoes_texto.grid(row=6, column=0, columnspan=3, padx=5, pady=5)

        arquivos_label = tk.Label(self.tab1, text='Arquivos para enviar ao assistente:')
        arquivos_label.grid(row=7, column=0, padx=5, pady=5)
        
        botao_arquivos = tk.Button(self.tab1, text='Adicionar', command=self.adicionar_arquivo)
        botao_arquivos.grid(row=7, column=1, padx=5, pady=5)

        self.botao_criar = tk.Button(self.tab1, text='Criar', background='lightgreen', command=self.criar_assistente)
        self.botao_criar.grid(row=8, column=2, padx=5, pady=15)    

        # Aba 2 - Chat com assistente
        self.carregar_assistentes()
        self.thread_id = ''
        self.resposta_assistente = ''
        self.row_tab2 = 0
        self.opcoes_assistentes = tk.StringVar()
        self.opcoes_assistentes.set('')
        lista_assistentes_label = tk.Label(self.tab2, text="Assistentes de IA registrados:")    
        lista_assistentes_label.grid(row=0, column=0, padx=5, pady=5)
        assistentes_op = tk.OptionMenu(self.tab2, self.opcoes_assistentes, *self.assistentes)
        assistentes_op.grid(row=1, column=0, padx=5, pady=5)
        self.texto_chat = tk.Text(self.tab2, width=70, height=30, wrap=tk.WORD, state=tk.DISABLED)
        self.texto_chat.grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        self.prompt = tk.Entry(self.tab2, width=70)
        self.prompt.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        self.botao_enviar = tk.Button(self.tab2, text='Enviar', command=lambda: self.chat_assistente(self.prompt.get(), self.assistentes[self.opcoes_assistentes.get()], self.thread_id))
        self.botao_enviar.grid(row=3, column=2, padx=5, pady=5)
        
        self.janela_principal.mainloop()

    def criar_assistente(self):
        try:
            client = OpenAI(api_key=self.api_entry.get())
        except Exception as e:
            self.janela_erro(erro=e)
        assistant = client.beta.assistants.create(
        name=self.nome_entry.get(),
        instructions=f"""
                {self.instrucoes_texto}
            """,
        model=self.opcoes_var.get(),
        tools=[{"type": "file_search"}],
        )        
        self.id_assistente = assistant.id
        vector_store = client.beta.vector_stores.create(name=self.nome_entry.get())
        file_streams = [open(path, "rb") for path in self.arquivos]
        client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams)
        assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},) 
        self.salvar_dados_assistente(nome=self.nome_entry.get(), id=assistant.id)  
        self.assistente_id = assistant.id     
        popup_sucesso = tk.Toplevel(self.janela_principal)
        popup_sucesso.title("Assistente de IA construído")
        label_sucesso = tk.Label(popup_sucesso, text=f'ID: {assistant.id}')
        label_sucesso.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        botao_ok = tk.Button(popup_sucesso, text='Ok', command=popup_sucesso.destroy)
        botao_ok.grid(row=1, column=1, padx=5, pady=5, sticky='w')
    
    def chat_assistente(self, prompt: str, assistente_id: str, thread_id: str):
        try:
            chaves = dotenv_values('.env')
            api = chaves['OPENAI_APIKEY']
            client = OpenAI(api_key=api)            
        except Exception as e:
            self.janela_erro(erro=e)
            print(e)        
        if thread_id == '':        
            thread = client.beta.threads.create(
            messages= [
                {
                    'role': 'user',
                    'content': prompt,
                }
            ]
            )                           
        else:        
            thread = client.beta.threads.retrieve(thread_id=thread_id)
            thread_message = client.beta.threads.messages.create(
                thread_id = thread_id,
                role = "user",
                content = prompt,
                )
        self.thread_id = thread.id
        assistente = client.beta.assistants.retrieve(assistant_id=assistente_id)
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistente.id)            
        messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
        message_content = messages[0].content[0].text
        self.resposta_assistente = message_content.value
        self.adicionar_mensagem(mensagem=self.resposta_assistente)
        return message_content.value

        
    def adicionar_arquivo(self):
        caminho = filedialog.askopenfilename(parent=self.tab1, filetypes=[("PDF files", "*.pdf")]) 
        if caminho:
            self.arquivos.append(caminho)
            novo_arquivo = tk.Label(self.tab1, text=caminho)
            novo_arquivo.grid(row=self.row + 1, column=0, padx=5, pady=5)
            self.row += 1
    
    def salvar_dados_assistente(self, nome: str, id: str, env_file=".env"):
        with open(env_file, 'a') as file:
            file.write(f"\n{nome}={id}")
        load_dotenv()
    
    def registro_api_key(self, env_file='.env'):
        with open(env_file, 'r') as file:
            content = file.read()   
        if "OPENAI_APIKEY" not in content:
            with open(env_file, 'a') as file:
                file.write(f"OPENAI_APIKEY={self.api_entry.get()}\n")
        load_dotenv()
    
    def carregar_api_key(self):
        chaves = dotenv_values('.env')
        for chave, valor in chaves.items():
            if chave == 'OPENAI_APIKEY':
                self.api_entry.delete(0, tk.END)  
                self.api_entry.insert(0, valor)

    def carregar_assistentes(self):        
        chave = dotenv_values('.env')
        for chave,valor in chave.items():
            if chave != 'OPENAI_APIKEY':
                self.assistentes[chave] = valor  
        print(self.assistentes)          

    def adicionar_mensagem(self, mensagem):
        self.texto_chat.config(state=tk.NORMAL)  # Permite edição temporária do widget
        self.texto_chat.insert(tk.END, mensagem + "\n")  # Adiciona a nova mensagem no final
        self.texto_chat.config(state=tk.DISABLED)  # Impede edição do texto
        self.texto_chat.see(tk.END)  # Rola até a última mensagem
    
    def janela_erro(self, erro: str):
        popup_erro = tk.Toplevel(self.jalela_enviar)
        popup_erro.title("Erro")
        label_erro = tk.Label(popup_erro, text=f'{erro}')
        label_erro.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        botao_ok = tk.Button(popup_erro, text='Ok', command=popup_erro.destroy)
        botao_ok.grid(row=1, column=1, padx=5, pady=5, sticky='w')
            
     
janela = JanelaPrincipal()