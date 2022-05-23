#https://info.dengue.mat.br/services/api
#https://info.dengue.mat.br/tutorial_api_r/
#https://info.dengue.mat.br/api/alertcity/?geocode=3548906&disease=dengue&format=json&ew_start=17&ey_start=2022&ew_end=21&ey_end=2022
#https://github.com/AlertaDengue

shhh <- suppressPackageStartupMessages # It's a library, so shhh!
options(warn=-1)

shhh(library(tidyverse))
shhh(library(magrittr))
shhh(library(RCurl))
shhh(library(lubridate))

print(paste0("* LOG-Rnow: ",format(Sys.time(),"%d-%h-%Y, %A às %H:%M")))

path.base = '/home/rafael/workspace/dash-covid-sanca/'
# Get data from api
url.base = 'https://info.dengue.mat.br/api/alertcity/?geocode=3548906&disease=dengue&format=csv'
date.epweek = week(today())
url.full = paste(url.base,
                 '&ew_start=', toString(date.epweek-4*4), '&ew_end=', toString(date.epweek+1),
                 '&ey_start=', toString(year(today())-1), '&ey_end=', toString(year(today())),
                 sep='')
data.raw = getURL(url.full)
tf.data.raw = as_tibble(read_csv(data.raw, show_col_types = F)) %>% arrange(data_iniSE)
#glimpse(tf.data.raw)

# Pre-processa dados recebidos
tf.data.raw$data_endSE = tf.data.raw$data_iniSE + 7  # The original date refeers to the start of EpWeek
tf.data.raw$casos %<>% as.integer
tf.data.raw$casos_est %<>% as.integer
tf.data.raw$casos_est_min %<>% as.integer
tf.data.raw$casos_est_max %<>% as.integer

#if (num.updated == 0 && num.new == 0){
#  must.update = FALSE
#} else {
  must.update = TRUE
#}

if (must.update){
#  Gerar plot
pltdata = tf.data.raw %>% select(data_endSE, casos, casos_est, casos_est_min, casos_est_max)
lenght.now = 8
lastyear = as.Date(today() - 365)
#Sys.setenv(LANG = "pt")  # Set lang in the sh calling this script
cap.update = paste0("* Última atualização: ",format(Sys.time(),"%A, %d-%h-%Y às %H:%M"))
#cap.param = paste0("* Parâmetros do nowcasting (McGough et al 2020): dist=\"NB\"; window=45; maxdelay=30; trim=1; CI=80%")
cap.source = paste0("* Fonte dos dados: https://info.dengue.mat.br",
                    "   /   ",
                    "Fonte da imagem: https://rahcor.github.io/dados-covid-sanca/")
#x11(width = 12, height = 5); ggplot(pltdata) +
ggplot(pltdata) +
  theme_bw() +
  theme(plot.background = element_rect(fill="lightgray"),
        text=element_text(size=16,  family="Nunito", color = 'black'),
        axis.text = element_text(color = 'black'),
        panel.grid.minor = element_blank(),
        panel.grid.major = element_line(linetype = 'dotted', size=0.35, color='darkgray'),
        plot.title = element_text(hjust = 0.5),
        axis.title = element_blank(),
        plot.caption = element_text(hjust=c(0,1.025)), #,vjust=c(1.25,1.4)),
        legend.title=element_blank(),
        legend.margin=margin(c(1,5,5,5)),
        legend.position = c(0.16, 0.85),
        legend.spacing.y = unit(2, "mm"),
        legend.background = element_rect(fill = "white", color = "lightgray"),
  ) +
  # geom_area(data = tail(pltdata,22), aes(x = onset_date, y = estimate),
  #           alpha = 0.33, fill = 'lightgray') +
  geom_area(data = pltdata,
            aes(x = data_endSE, y = casos, fill='Casos notificados', color='Casos notificados'),
            alpha = 0.6) +
  geom_line(data = head(pltdata, -lenght.now+1),
            aes(x = data_endSE, y = casos, colour='Casos consolidados e estimados'),
            lwd = 0.75) +
  # geom_ribbon(data = tail(pltdata, lenght.now),
  #             aes(x=data_endSE,
  #                 ymin=casos_est_min,
  #                 ymax=casos_est_max,
  #                 fill = "Nowcasting (CI 95%)",
  #                 color = "Nowcasting (CI 95%)"),
  #             lwd = 0.85) +
  geom_line(data = tail(pltdata, lenght.now),
            aes(x = data_endSE,
                y = casos_est),
                color = "red", lwd = 0.75) +
  scale_x_date(breaks = "1 month",
               labels = scales::label_date_short(),
               minor_breaks = "1 week",
               limits = c(lastyear-7*(lenght.now+4), today())) + 
  scale_y_continuous(position = "right", breaks = seq(0,1.1*max(pltdata$casos_est),by=25),
				limits = c(0,1.1*max(pltdata$casos_est))) +
  coord_cartesian(expand = FALSE) +
  scale_colour_manual("", 
                      values = c("Casos notificados"="mistyrose",
                                 "Casos consolidados e estimados"="red")) +
  scale_fill_manual("", 
                      values = c("Casos notificados"="mistyrose",
                                 "Casos consolidados e estimados"="white")) +
  labs(caption = c(paste0(cap.update,"\n",cap.source),
                   format(Sys.time(),"(%d-%h)"))) +
  ggtitle("Dengue: casos semanais incluindo nowcasting")

  ggsave(paste(path.base, "dengue-nowcasting.png", sep = ''), width = 12, height = 5, dpi = 100)
  print("Plot saved!")
}

print("Rscript for dengue complete.")

#  Commit imagem [BASH]
