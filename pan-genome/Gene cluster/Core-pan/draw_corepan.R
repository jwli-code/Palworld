require(gridExtra)
library(RColorBrewer)
library(ggpubr)
library(ggsci)
library(ggstatsplot)

library(ggplot2)

PanG_file="C:/Users/13691/Documents/R脚本/TE/Bna_PanGenomeData"
PanG=read.delim(PanG_file,sep='\t')
colnames(PanG)<-c('GenomeNum','PanGenomeSize','CoreGenomeSize')
# 将第三列和第四列都除以1000
PanG$PanGenomeSize <- PanG$PanGenomeSize /1000
PanG$CoreGenomeSize <- PanG$CoreGenomeSize / 1000
PanG[,'GenomeNum']<-factor(PanG[,'GenomeNum'],levels = seq(1,14))
dat1=PanG[,c('GenomeNum','PanGenomeSize')]
colnames(dat1)<-c('GenomeNum','GenomeSize')
dat1[,'group']<-'PanGenome'
dat2=PanG[,c('GenomeNum','CoreGenomeSize')]
colnames(dat2)<-c('GenomeNum','GenomeSize')
dat2[,'group']<-'CoreGenomeSize'
dat=rbind(dat1,dat2)

mytheme<-theme(axis.text.x = element_text(angle = 0,size=14),
               plot.title = element_text(hjust = 0.5),
               panel.grid.major =element_blank(), 
               panel.grid.minor = element_blank(),
               panel.background = element_blank(),
               axis.line = element_line(color = "black", size = 1), 
               axis.ticks.y = element_line(size = 1),  # 调整纵轴刻度线粗细
               axis.ticks.x = element_line(size = 1),
               axis.text.y = element_text(angle = 0,size = 14),
               axis.title.x = element_text(size = 20), # 设置x轴标签的字体大小
               axis.title.y = element_text(size = 20))


nums=seq(1,14)
pan_size=c()
core_size=c()
for(i in nums){
  pan_size=append(pan_size,median(dat1[dat1$GenomeNum==i,'GenomeSize']))
  core_size=append(core_size,median(dat2[dat2$GenomeNum==i,'GenomeSize']))
}
sum_dat1=data.frame(GenomeNum=nums,GenomeSize=pan_size)
sum_dat2=data.frame(GenomeNum=nums,GenomeSize=core_size)


p=ggplot(data=dat1,aes(GenomeNum,GenomeSize))+
  #geom_point(alpha = 0.7,size=1.5, position = "jitter", aes(colour = TEgroup)) +
  scale_color_npg()+scale_fill_npg()+
  stat_boxplot(geom ='errorbar', width = 0.3, color="#00A087")+
  geom_boxplot(width=0.5, color="#00A087", outlier.color = NA, outlier.shape = NA)+
  
  geom_point(data=sum_dat1,mapping = aes(GenomeNum,GenomeSize),size=1.5, color="#00A087") +
  geom_line(data=sum_dat1,mapping = aes(GenomeNum,GenomeSize), color="#00A087") +
  
  stat_boxplot(data=dat2,mapping = aes(GenomeNum,GenomeSize), color="#F39B7F",geom ='errorbar', width = 0.3)+
  geom_boxplot(data=dat2,mapping=aes(GenomeNum,GenomeSize), color="#F39B7F", width=0.5,
               outlier.color = NA, outlier.shape = NA)+
  
  geom_point(data=sum_dat2,mapping = aes(GenomeNum,GenomeSize),size=1.5, color="#F39B7F") +
  geom_line(data=sum_dat2,mapping = aes(GenomeNum,GenomeSize), color="#F39B7F") +
  xlab("Genome Number")+mytheme+ylim(0, 120)+ylab("Gene Cluster Number (K)")+
  mytheme
p

ggsave("C:/Users/13691/Documents/R脚本/TE/Bna-pan-core.pdf", plot = p, device = "pdf", width = 6, height = 5, bg = "white")
pdf(p,6,6)
p
dev.off()
