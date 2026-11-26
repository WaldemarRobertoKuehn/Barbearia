# NORDEN — MVP demonstrativo

Aplicação local responsiva para o salão masculino NORDEN. A identidade usa tokens da paleta Grafite Premium: grafite `#1F1F23`, ônix `#0B0B0D`, taupe `#8C8176`, bronze `#8E6B47` e Soft Stone `#E7E2DB`.

## Executar

Requisitos: Node.js 20+ e Python 3 com módulo `sqlite3` (a biblioteca padrão do Python).

```powershell
npm start
```

Acesse http://localhost:4173. O servidor escuta somente em `127.0.0.1`. O banco SQLite `norden.sqlite` é criado na primeira inicialização. Para apagar os dados demonstrativos e recriar o seed, pare o servidor e exclua esse arquivo local.

## Perfis demonstrativos

Use o seletor no cabeçalho para alternar entre cliente e gestão. Cliente inicial: Lucas Martins (`lucas@norden.demo`). Gestão/profissional: Rafael Almeida (`rafael@norden.demo`). A troca de perfil é uma simulação de interface e **não é autenticação**. Não insira dados pessoais reais; não exponha esta aplicação à rede.

## O que funciona

- Catálogo público de serviços e produtos fictícios.
- Agendamento conectado ao backend SQLite, com verificação de sobreposição por profissional e duração do serviço.
- Cancelamento mantém o registro e pode gerar sugestão de encaixe; realocação é explícita e mantém o horário original quando recusada.
- Painel de equipe com agenda, clientes, Flow e ações de atendimento.
- Conclusão do atendimento, registro dos produtos realmente usados e publicação das orientações Care para a jornada do cliente.
- Loja, carrinho em memória do navegador, retirada ou entrega estimada, criação do pedido e baixa de estoque.
- Atualização de status dos pedidos pela equipe e edição demonstrativa das preferências do cliente.
- Registro básico de ações no banco.

## Limites conhecidos

- Este é um MVP/protótipo local, não um sistema pronto para uso comercial.
- Seletor de perfil não substitui autenticação; a API não é segura para dados reais ou exposição em rede. Não há senha, sessão, recuperação de conta nem autorização com identidade validada.
- Agenda usa slots de demonstração e verifica conflitos existentes, mas não configura jornada de trabalho, feriados, intervalos, fuso/expiração ou concorrência transacional completa.
- Flow ilustra uma regra determinística simples; não envia notificações e não implementa janela configurável ou fluxo completo entre dois clientes.
- Entrega calcula distância informada vezes R$ 2,50/km, valor apenas ilustrativo. Não há mapa/rota. Pagamento é presencial; não há cobrança online.
- Sem integração de e-mail/SMS/WhatsApp, gateway, armazenamento de imagens, avaliações ou implantação.
- O projeto inclui `assets/norden-logo.svg`, reconstrução vetorial demonstrativa com base na referência enviada. Para fidelidade exata, substitua o SVG pela arte mestre oficial mantendo esse caminho.

## Decisões de demonstração

Serviços, profissionais, produtos, preços, estoque e perfis iniciais são fictícios e editáveis no seed em `database.py`. A imagem hero é uma composição CSS sem fotografia de estabelecimento real. O tema usa a paleta fornecida pelo usuário.

## Estrutura

- `server.js`: servidor HTTP Node e API local.
- `database.py`: schema SQLite, seed e operações do backend.
- `app.js`, `styles.css`, `index.html`: interface e interações responsivas.
- `norden.sqlite`: banco criado na execução (não versionar dados pessoais).

Nenhum teste automatizado foi criado ou executado nesta entrega.
