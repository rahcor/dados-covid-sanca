#  API req ultimos dados [BASH/CURL]

shhh <- suppressPackageStartupMessages # It's a library, so shhh!
shhh(library(tidyverse))
shhh(library(magrittr))
shhh(library(jsonlite))

shhh(library(tsibble))
shhh(library(xts))
shhh(library(padr))
shhh(library(lubridate))
shhh(library(scales))

shhh(library(RcppRoll))
shhh(library(NobBS))

options(warn=-1)
print(paste0("* LOG-Rnow: ",format(Sys.time(),"%d-%h-%Y, %A às %H:%M")))

path.base = '/home/rafael/workspace/dash-covid-sanca/'
# Read json files
now.input.json = as_tibble(fromJSON(paste(path.base, 'db-sintomas.json', sep=''), flatten = TRUE))
temp.update = fromJSON(paste(path.base, 'update.json', sep=''), flatten = TRUE)
tf.update = as_tibble(temp.update$hits$hits)
## Adjust column names
names(tf.update) = sub('_source.', '', names(tf.update))
names(tf.update) = sub('_', '', names(tf.update))

# Pre-processa dados recebidos
## Filter parts of interest
tf.covid = now.input.json
tf.update %<>% select(names(tf.covid))

# Atualiza
## Map indexes of identical ids
eqid.in.orig = tf.covid$sourceid %in% tf.update$sourceid
eqid.in.update = tf.update$sourceid %in% tf.covid$sourceid
num.equal = sum(eqid.in.update)
num.new = sum(!eqid.in.update)
common1 = arrange(tf.covid[eqid.in.orig,], sourceid)
common2 = arrange(tf.update[eqid.in.update,], sourceid)
num.updated = sum(common1$dataAtualizacao != common2$dataAtualizacao)
if (num.updated != 0){
  ## Always replace old data for matching id, either updated or not
  update.sourceids = tf.update[eqid.in.update,]$sourceid
  for (srcid in update.sourceids) {
    tf.covid[tf.covid$sourceid == srcid,] = tf.update[tf.update$sourceid == srcid,]
  }
}
if (num.new != 0){
  ## Include new ids
  tf.covid = bind_rows(tf.covid,tf.update[!eqid.in.update,])
}

if (num.updated == 0 && num.new == 0){
  must.update = FALSE
} else {
  must.update = TRUE
}

# Save db in a json file
if (must.update){
 write(toJSON(tf.covid[order(tf.covid$dataInicioSintomas, decreasing = TRUE),],pretty = 1),
             paste(path.base, "db-sintomas.json", sep=''))
 print("Database was written to json.")
}
print(paste0("num.updated = ",num.updated, "; num.new = ",num.new))

# Process data to input
## Adjust date format
now.input = tf.covid %>%
               mutate(dataInicioSintomas = as.Date(dataInicioSintomas, format = "%Y-%m-%d"),
                      dataNotificacao = as.Date(dataNotificacao, format = "%Y-%m-%d"),
                      dataTeste = as.Date(dataTeste, format = "%Y-%m-%d"),
                      dataTesteSorologico = as.Date(dataTesteSorologico, format = "%Y-%m-%d"),
                      dataRegistro = as.Date(dataRegistro, format = "%Y-%m-%d"),
                      dataAtualizacao = as.Date(dataAtualizacao, format = "%Y-%m-%d"),
                      dataEncerramento = as.Date(dataEncerramento, format = "%Y-%m-%d"))
## Get last date as confirmation date
now.input %<>% mutate(dataEncerramento = pmax(
                      dataNotificacao,
                      dataTeste,
                      dataRegistro,
                      dataTesteSorologico,
                      na.rm = TRUE)
                      ) %>%
                      drop_na(c('dataInicioSintomas', 'dataEncerramento'))

if (must.update){
#  Rodar NobBS
## Delays histogram
delays.hist = hist(as.integer(now.input$dataEncerramento - now.input$dataInicioSintomas),
                   xlim = c(0,40), breaks = 500, freq = FALSE,
                   xlab = "Atraso [dias]", ylab = "Frequência relativa",
                   main = NULL)
now.units = "1 day"
now.windowsize = 45  # [same unit as now.unit] the timespan for nowcasting (obscovid = 40)
now.trim = 3  # [days] (as.Date increment by days)
now.maxdelay = 30  ## [same unit as now.unit]  must be less than now.windowsize
## Run nowcasting
now.inputdf = as.data.frame(now.input[order(now.input$dataInicioSintomas),]) # Unordered input throws error: https://github.com/renatocoutinho/NobBS/commit/ded3195b1d2ea424e4b0ceabf59d3c19cf60c893
now.output = NobBS(data = now.inputdf[,c('dataInicioSintomas','dataEncerramento')],
                   now = max(now.inputdf$dataInicioSintomas, na.rm = TRUE) - now.trim,
                   onset_date = "dataInicioSintomas",
                   report_date = "dataEncerramento",
                   units = now.units,
                   moving_window = now.windowsize,
                   max_D = now.maxdelay,
                   quiet = TRUE,
                   specs = list("dist"="NB",
                     "conf"=0.80,
                     "beta.priors"=delays.hist$density[1:(now.maxdelay+1)])
                   )
print("Nowcasting complete!")
}

if (must.update){
#  Gerar plot
pltdata = now.input %>%
  group_by(dataInicioSintomas) %>%
  summarise(frequency = n()) %>%
  pad(interval = 'day') %>%
  fill_by_value(value = 0)
pltdata$avg7 = roll_mean(pltdata$frequency, n = 7, align = "center", fill = NA)
pltdata[pltdata$dataInicioSintomas %in% now.output$estimates$onset_date ,colnames(now.output$estimates)] <- as_tibble(now.output$estimates)
pltdata$avg7now = roll_mean(pltdata$estimate, n = 7, align = "center", fill = NA)
today = max(now.inputdf$dataInicioSintomas, na.rm = TRUE)
lastyear = as.Date(today - 365)
#Sys.setenv(LANG = "pt")  # Set lang in the sh calling this script
cap.update = paste0("* Última atualização: ",format(Sys.time(),"%A, %d-%h-%Y às %H:%M"))
cap.param = paste0("* Parâmetros de nowcasting: dist=\"NB\"; windowsize = 45; maxdelay = 30; CI = 80%")
cap.source = paste0("* Fonte dos dados: https://opendatasus.saude.gov.br/dataset/casos-nacionais",
                    "   /   ",
                    "Fonte da imagem: https://rahcor.github.io/dados-covid-sanca/")
#x11(); ggplot(pltdata) +
ggplot(pltdata) +
  theme_bw() +
  theme(plot.background = element_rect(fill="lightgray"),
        text=element_text(size=16,  family="Nunito", color = 'black'),
        axis.text = element_text(color = 'black'),
        panel.grid.minor = element_blank(),
        panel.grid.major = element_line(linetype = 'dotted', size=0.35, color='darkgray'),
        plot.title = element_text(hjust = 0.5),
        axis.title = element_blank(),
        plot.caption = element_text(hjust=0),
        legend.title=element_blank(),
        legend.margin=margin(c(1,5,5,5)),
        legend.position = c(0.16, 0.85),
        legend.spacing.y = unit(2, "mm"),
        legend.background = element_rect(fill = "white", color = "lightgray"),
  ) +
  # geom_area(data = tail(pltdata,22), aes(x = onset_date, y = estimate),
  #           alpha = 0.33, fill = 'lightgray') +
  geom_area(aes(x = dataInicioSintomas, y = frequency, fill='Casos diários por início de sintoma', color='Casos diários por início de sintoma'),
            alpha = 0.6) +
  geom_line(data = pltdata[pltdata$dataInicioSintomas < as.Date(today - 23),],
            aes(x = dataInicioSintomas, y = avg7, colour='Média móvel de 7 dias centralizada', fill='Média móvel de 7 dias centralizada'),
            size = 0.75) +
  geom_ribbon(data = tail(pltdata,30),
              aes(x=onset_date,
                  ymin=roll_mean(lower, n = 7, align = "right", fill = NA),
                  ymax=roll_mean(upper, n = 7, align = "right", fill = NA),
                  fill = "Nowcasting (média móvel de 7 dias)",
                  color = "Nowcasting (média móvel de 7 dias)"),
              alpha=0.8) +
  geom_line(data = tail(pltdata,30),
            aes(x = onset_date,
                y = roll_mean(estimate, n = 7, align = "right", fill = NA)),
            color = "white", size = 0.35, linetype='dotted') +
  scale_x_date(breaks = "1 month",
               labels = scales::date_format("%b\n%Y"),
               minor_breaks = "1 week",
               limits = c(lastyear, today)) + 
  scale_y_continuous(position = "right", breaks = seq(0,max(pltdata$frequency),by=25)) +
  coord_cartesian(expand = FALSE) +
  scale_colour_manual("", 
                      values = c("Casos diários por início de sintoma"="mistyrose",
                                 "Média móvel de 7 dias centralizada"="red",
                                 "Nowcasting (média móvel de 7 dias)"=NA)) +
  scale_fill_manual("", 
                      values = c("Casos diários por início de sintoma"="mistyrose",
                                 "Média móvel de 7 dias centralizada"=NA,
                                 "Nowcasting (média móvel de 7 dias)"="red")) +
  labs(caption = paste0(cap.update,"\n",cap.param,"\n",cap.source)) +
  ggtitle("Nowcasting dos casos diários por data de início dos sintomas")

  ggsave(paste(path.base, "nowcasting.png", sep = ''), width = 12, height = 5, dpi = 100)
  print("Plot saved!")
}

print("Rscript complete.")

#  Commit imagem [BASH]
