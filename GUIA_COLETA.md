# Guia de coleta — filas dos caixas do mercado

## O sistema que esta versão representa
Uma fila comum que alimenta caixas convencionais e/ou totens, por ordem de chegada (FIFO), sem prioridades ou abandono, com quantidade de cada tipo constante no período. Os postos são considerados equivalentes dentro de cada tipo, e cada cliente mantém a modalidade observada C ou CA. Confirme isso no local. Se cada caixa tem sua própria fila, registre a fila de cada cliente e não junte todas como se fossem uma só. A aplicação atual aceita uma fila por análise; o modelo precisará ser adaptado para representar trocas entre filas, prioridades, caixas rápidos ou abertura e fechamento de caixas.

## Antes de ir
- Combine a observação com o responsável pelo estabelecimento. Não colete nomes, rostos, documentos, dados de cartões ou compras identificáveis.
- Escolha uma posição de onde seja possível reconhecer chegada à fila, início e fim do atendimento. Se uma pessoa não consegue acompanhar todos os caixas, delimite um caixa ou distribua observadores e sincronize os relógios.
- Faça um piloto de 15 a 20 minutos para verificar se os registros são possíveis. Como planejamento inicial, reserve 60 a 90 minutos para o pico e, se possível, repita em outro dia e compare um período de menor movimento. Isso é sugestão de coleta, não exigência do professor nem garantia de amostra suficiente.
- Use relógios sincronizados com precisão de segundos. Não arredonde tudo para minutos: atendimentos curtos podem ficar com duração zero.

## Metadados obrigatórios de cada sessão
Anote em um registro separado do CSV:

| Dado | Como registrar |
| --- | --- |
| Identificação da sessão | Ex.: S01; use IDs únicos caso consolide arquivos |
| Data e local | Nome ou pseudônimo do mercado; a data real da visita |
| Início e fim da janela de chegadas | Horários exatos, inclusive trechos em que ninguém chegou |
| Fim do acompanhamento | Horário em que o último cliente da janela terminou |
| Responsáveis pela observação | Identificação dos pesquisadores |
| Organização das filas | Única, separadas, rápidas, prioritárias; regra de atendimento |
| Caixas e capacidade | IDs dos caixas e horários de abertura/fechamento/pausas |
| Estado no início | Pessoas esperando e em atendimento em cada fila/caixa |
| Estado no fim | Pessoas esperando e em atendimento na hora de corte |
| Intercorrências | Falta de sistema, troca de operador, intervalo, promoção, mudança de fila, desistência |

Se a quantidade de caixas mudar, delimite sessões de capacidade constante. Não considere um caixa que esteve fechado como disponível o período inteiro.

## Um registro por cliente ou grupo de compra
Uma compra que passa junta pelo caixa é uma unidade de atendimento. Não conte cada acompanhante como um cliente separado.

| Coluna exata no CSV | Obrigatória | Definição |
| --- | --- | --- |
| id | Sim | Código anônimo único, por exemplo S01-001 |
| chegada | Sim | Momento de entrada na fila, não de entrada no mercado |
| inicio_atendimento | Sim | Momento em que começa a ser atendido no caixa, segundo o critério definido no piloto |
| fim_atendimento | Sim | Momento em que o caixa fica disponível para o próximo, incluindo pagamento e eventual conclusão do atendimento |
| caixa | Sim | C para convencional ou CA para autoatendimento; pode repetir em vários registros |
| fila | Sim | F1 para fila única; filas independentes devem manter IDs distintos |
| origem | Preencher | REAL na pesquisa; FICTICIO apenas em testes |
| observacoes | Opcional | Interrupção, duração aproximada ou ocorrência que ajude a interpretar o registro |

Formato das datas: `2026-11-03 18:02:35`, sempre incluindo a data e sem fuso. Separador do arquivo: ponto e vírgula. Use o cabeçalho de `dados/modelo_coleta_por_tipo.csv`. Não altere os nomes das colunas. Uma linha por atendimento. O CSV fictício é exemplo de estrutura, não uma observação real.

## Como lidar com o início e o fim
1. Preferencialmente comece a acompanhar antes do pico, com a fila vazia, e registre os clientes até o horário definido.
2. Caso já existam pessoas na fila no início, conte-as e registre o estado. Se conseguir, observe antes da janela para conhecer suas chegadas e os atendimentos em andamento.
3. Ao encerrar a janela de chegadas, pare de incluir novas chegadas, mas acompanhe quem já foi incluído até o fim. Registre também a quantidade de pessoas restantes na hora do corte.
4. Não descarte quem demorou mais nem estime horários desconhecidos para completar a tabela. Guarde registros incompletos separadamente e indique o motivo.
5. A versão atual exige registros completos. Se os clientes iniciais não têm histórico conhecido, os indicadores temporais podem ficar subestimados. Não os apresente como medição completa: escolha uma janela com acompanhamento completo ou adapte o tratamento de censura antes da análise final.

As médias de espera e tempo no sistema usam os clientes que chegaram dentro da janela [início, fim). Esses clientes podem terminar depois do fim. Fila média e ocupação usam apenas a janela informada, incluindo clientes anteriores com histórico completo. Não espere que uma única janela curta reproduza exatamente relações de regime estacionário.

## Conferências no local
- Chegada ≤ início < fim em todos os registros.
- Um caixa não atende duas compras ao mesmo tempo.
- Todos os atendimentos do recorte devem estar representados, inclusive quem não esperou.
- Conte a fila e os caixas ocupados a cada 5 minutos como verificação independente dos registros. Anote esses controles com horário em um registro separado.
- Se houver abandono, prioridade, troca de fila ou falta de observação, registre horário e ocorrência separadamente. Esta primeira versão não modela esses comportamentos; eles precisam ser considerados na análise.
- Não use nomes de clientes ou funcionários para identificar recursos.

## Dados adicionais para a parte de simulação ampliada
Mapeie antes o fluxo real e consulte o professor sobre o triplo de atividades/recursos. Para cada atividade incluída, observe entrada na fila, início, fim, recurso utilizado e destino seguinte, vinculados ao mesmo ID anônimo. Conte recursos paralelos e seus horários de disponibilidade. Não crie atividades só para alcançar uma contagem: o modelo deve refletir o mercado.

## Como usar a coleta na página
1. Exporte/guarde o CSV original e os metadados da sessão.
2. Inicie o servidor e importe seu CSV.
3. Ajuste a data, início, fim e quantidade de caixas reais. As datas do exemplo não são alteradas automaticamente na importação.
4. Clique em Calcular e comparar. Revise mensagens e compare as contagens com as conferências de campo.
5. Só depois investigue hipóteses do modelo, valide a simulação e compare cenários hipotéticos. A primeira versão usa chegadas Poisson constantes, hipótese que precisa ser examinada especialmente no pico.

## Identificação da operação na interface

A coluna opcional `estabelecimento` pode conter o nome ou pseudônimo da operação, repetido em cada registro (por exemplo Angelone). O nome aparece no topo do gestor. A coluna `caixa` foi preservada para compatibilidade: em outro tipo de serviço ela identifica o posto ou atendente, com IDs estáveis. O exemplo Angelone permanece inteiramente FICTICIO.

## Configuração de caixas convencionais e totens
A aplicação inicia sem dados. Envie o CSV, classifique cada identificador e informe as quantidades disponíveis de cada tipo. Não são necessárias novas colunas: a classificação é feita na configuração e não altera os registros originais.
Na coleta, registre quais IDs são convencionais e quais são totens e seus horários de disponibilidade. Nos totens, cronometre até liberar a máquina; anote necessidade de auxílio e funcionário compartilhado. Esse auxílio compartilhado ainda não é modelado.
Para comparar capacidade sem amostra de um tipo, informe uma hipótese de duração relativa. Não classifique atendimentos convencionais como autoatendimento para completar a amostra. A modalidade de cada cliente é preservada nesta versão. Filas independentes e restrições exigem adaptação.
Confira a janela real: a sugestão usa registros, sem conhecer o início/fim efetivos da observação.

## Campos opcionais para importar uma massa de teste
`tipo_caixa` aceita normal ou self e deve ser consistente por ID. `inicio_observacao` e `fim_observacao` podem declarar a janela no arquivo; a tela permite conferi-la. `itens` é informativo e não restringe elegibilidade na simulação. `origem=SINTETICO` indica dados gerados; mantenha REAL somente para observações realizadas no local. A massa Angeloni_pico.csv não é fonte de evidência sobre o estabelecimento.


## Atualização: coleta por tipo e decisão de capacidade
Use dados/Angeloni_pico_por_tipo.csv para teste e dados/modelo_coleta_por_tipo.csv como cabeçalho. Na coluna caixa informe somente C (convencional) ou CA (autoatendimento). Não precisa identificar o equipamento físico. Chegada, início e fim continuam necessários para medir a espera observada e a duração do serviço. Registre a fila e os horários reais, sem inventar tempos desconhecidos.

capacidade_convencional e capacidade_autoatendimento são colunas opcionais repetidas por sessão: informam a capacidade da coleta e sugerem as quantidades iniciais da configuração. A escolha de capacidade para projetar é revisável na tela. Dados antigos com IDs físicos continuam aceitos e podem ser classificados na configuração.

A projeção inicial mantém as chegadas, durações e tipos registrados e redistribui clientes entre todos os postos disponíveis daquele tipo, em ordem de chegada. A espera observada não muda quando a capacidade muda. A fila é FIFO dentro do tipo escolhido; não supomos migração entre tipos. Alterar demanda usa as repetições Poisson; a coluna Espera redistribuída conserva as chegadas e varia apenas capacidade/duração. Ocupação observada não é mostrada porque a capacidade projetada não comprova a capacidade histórica.

A reprodução inicial agora mostra a projeção redistribuída, sem postos artificiais sem dados. Não é uma reprodução literal dos antigos IDs. As alternativas Poisson mostram a primeira execução de 30, com tipos sorteados nas proporções da coleta. Modelagem de escolha de modalidade, filas independentes e ajuda compartilhada ainda depende do estudo real.
