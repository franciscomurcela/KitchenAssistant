#Associação de perguntas para métricas para dashboard.py
# Cada métrica tem perguntas associadas (sim/não e escala)

metric_questions = {
    "facil_de_usar": [
        # Perguntas sobre frustração, facilidade de interação e clareza na usabilidade
        "Foi fácil fazer o assistente entender que queria adicionar algo à despensa?",
        "Foi fácil fazer o assistente entender que queria remover algo da despensa?",
        "Nunca sentiu frustração ao tentar usar a despensa?",
        "Nunca sentiu frustração ao tentar usar a lista de compras?",
        "Foi fácil fazer o assistente entender que queria adicionar algo à lista?",
        "Conseguiu adicionar itens com quantidades específicas (ex: 2 tomates, 1 kg de arroz)?",
        "Já sentiu frustração ao tentar usar a lista de compras?",
        "Sente que a funcionalidade de lista de compras é fácil de usar?",
        "Numa escala de 1 a 5, o quanto você teve dificuldade em fazer o assistente entender que queria adicionar algo à lista?",
        "Numa escala de 1 a 5, o quanto foi fácil adicionar itens com quantidades específicas (ex: 2 tomates, 1 kg de arroz)?",
        "Numa escala de 1 a 5, o quanto você se sentiu frustrado ao tentar usar a lista de compras?",
        "Numa escala de 1 a 5, o quanto você considera fácil de usar a funcionalidade de lista de compras?"
    ],
    "estou_satisfeito": [
        # Satisfação com qualidade de respostas, funcionalidades e conteúdos
        "O assistente tem-lhe apresentado receitas do seu agrado?",
        "Está satisfeito com a variabilidade de receitas oferecidas pelo assistente?",
        "Considera que a qualidade das receitas apresentadas pelo assistente é adequada?",
        "A receita fornecida pelo assistente atendeu às suas expectativas?",
        "A funcionalidade da lista de compras é útil no seu dia a dia?",
        "O assistente forneceu uma quantidade adequada de informações sobre cada receita na lista?",
        "A lista de receitas foi organizada de uma maneira que facilitou sua escolha?",
        "Numa escala de 1 a 5, o quanto as receitas apresentadas pelo assistente foram do seu agrado?",
        "Numa escala de 1 a 5, o quão satisfeito está com a variabilidade das receitas oferecidas pelo assistente?",
        "Numa escala de 1 a 5, em que medida você considera que a qualidade das receitas apresentadas deveria ser maior?",
        "Numa escala de 1 a 5, o quanto a receita fornecida atendeu às suas expectativas?",
        "Numa escala de 1 a 5, o quanto a funcionalidade da lista de compras é útil no seu dia a dia?",
        "Numa escala de 1 a 5, o quanto a lista de receitas foi organizada de uma maneira que facilitou sua escolha?"
    ],
    "usaria_novamente": [
        # Intenção de reutilização de funcionalidades
        "Usaria novamente a função de pedir uma receita aleatória?",
        "Usaria novamente a função de pedir uma receita específica?",
        "Numa escala de 1 a 5, qual a probabilidade de você usar novamente a função de pedir uma receita aleatória?",
        "Numa escala de 1 a 5, qual a probabilidade de você usar novamente a função de pedir uma receita específica?"
    ],
    "comunica_bem": [
        # Clareza de linguagem, explicações, comandos e interações
        "O assistente foi claro ao explicar as funcionalidades?",
        "As instruções fornecidas pelo assistente foram úteis?",
        "Conseguiu perceber o que cada comando faz?",
        "Considera que os comandos estão bem descritos?",
        "A repetição do passo foi clara e fácil de entender?",
        "O assistente foi claro ao explicar o próximo passo?",
        "A apresentação da lista foi clara e fácil de entender?",
        "Conseguiu compreender a saudação do assistente?",
        "Numa escala de 1 a 5 o quão explícitas achou as instruções?",
        "Numa escala de 1 a 5 o quão esclarecedor foi o assistente ao explicar as funcionalidades?",
        "Numa escala de 1 a 5, o quão clara e fácil de entender foi a repetição do passo feita pelo assistente?",
        "Numa escala de 1 a 5, o quanto o assistente foi claro ao explicar o próximo passo?",
        "Numa escala de 1 a 5, o quanto as instruções fornecidas pelo assistente foram úteis?",
        "Numa escala de 1 a 5, o quanto você conseguiu perceber o que cada comando faz?",
        "Numa escala de 1 a 5, o quão bem descritos estavam os comandos?",
        "Numa escala de 1 a 5, o quão clara e fácil de entender foi a apresentação da lista de compras?",
        # VARIANTES para matching robusto
        "Numa escala de 1 a 5, que número atribuiria em relação ao seu entendimento sobre o que cada comando faz?",
        "Numa escala de 1 a 5 que numero atribuiria em relacao ao seu entendimento sobre o que cada comando faz",
        "Numa escala de 1 a 5, o quão úteis foram os comandos apresentados?",
        "Numa escala de 1 a 5 o quao uteis foram os comandos apresentados",
        "Toda a informação crítica foi apresentada na ajuda?",
        "Todas as informações importantes estavam presentes no passo repetido?",
    ],
    "faz_oque_quero": [
        # Avalia se o assistente compreendeu e executou corretamente os pedidos
        "Acha que os comandos apresentados lhe foram úteis?",
        "Quando pediu para repetir um passo, o assistente respondeu corretamente?",
        "Todas as informações importantes estavam presentes no passo repetido?",
        "Sentiu-se satisfeito com a forma como o assistente repetiu um passo?",
        "A receita apresentada corresponde ao tipo de prato que pediu?",
        "O assistente compreendeu corretamente o tipo de receita que solicitou?",
        "O conteúdo do e-mail estava claro e continha todos os itens?",
        "Numa escala de 1 a 5, em que medida os comandos disponibilizados atenderam às suas necessidades?",
        "Numa escala de 1 a 5, em que medida os comandos disponibilizados foram limitados para responder às suas questões?",
        "Numa escala de 1 a 5, o quão corretamente o assistente respondeu quando você pediu para repetir um passo?",
        "Numa escala de 1 a 5, em que medida você sentiu falta de alguma informação importante na repetição do passo?",
        "Numa escala de 1 a 5, o quanto você se sentiu frustrado com a forma como o assistente repetiu um passo?",
        "Numa escala de 1 a 5, o quanto a receita apresentada correspondeu ao tipo de prato que você pediu?",
        "Numa escala de 1 a 5, o quanto o assistente compreendeu corretamente o tipo de receita que você solicitou?",
        # VARIANTES para matching robusto
        "Acha que os comandos disponibilizados foram suficientes para as suas questões?",
        "Acha que os comandos disponibilizados foram limitados para as suas questoes",
        "Numa escala de 1 a 5, o quanto você se sentiu frustrado com a forma como o assistente repetiu um passo?",
        "Numa escala de 1 a 5 o quanto voce se sentiu frustrado com a forma como o assistente repetiu um passo",
    ]
}
