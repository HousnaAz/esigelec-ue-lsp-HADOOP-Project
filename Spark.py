from pyspark.sql.functions import monotonically_increasing_id, col, lag, trim, substring, when, udf,sqrt, pow, round,sum, lead
from pyspark.sql.types import StringType
from pyspark.sql.window import Window

# Chargement du fichier json origin
df = spark.read.json(sc.wholeTextFiles("file:///mnt/c/results2.json").values())

# Ajout du id pour chaque ligne
df = df.withColumn("id", monotonically_increasing_id()) 

# Déclaration de window qui permet d'utiliser la fonction sql fenètre
my_window = Window.partitionBy().orderBy("id") 

# Renommage et séparation des colonnes
df = df.withColumnRenamed( "Ball position" , "position" ) 
df = df.withColumnRenamed( "Ball state" , "state" )
df = df.withColumn( "x" , when(substring(trim(df.state),1,10).contains('n')==False,df["position"].getItem(0)).otherwise(0))
df = df.withColumn( "y" , when(substring(trim(df.state),1,10).contains('n')==False,df["position"].getItem(1)).otherwise(0))

# Recherche des values (état, position x y) de la ligne suivant ; ajout dans la ligne actuelle 
df = df.withColumn("nxt_state",lead(df.state).over(my_window)) 
df = df.withColumn("nxt_x",lead(df.x).over(my_window))
df = df.withColumn("nxt_y",lead(df.y).over(my_window))

# Reconnaissance des frames qui correspondant aux buts selon les critères suivantes: 
# 1. Un ball est détecté das le frame actuel mais disparaît dans le frame suivant
# 2. La position du ball est dans la zone porte de babyfoot (Cette zone n'est pas très precise pour l'instant)
df = df.withColumn("goal",when((substring(trim(df.state),1,10).contains('n')==False) & (substring(trim(df.nxt_state),1,10).contains('n')) & ( df.y>150) & (df.y<300)& ((df.x < 100) | (df.x >500)) , 1).otherwise(0))
df = df.withColumn("goal",lead(df.goal).over(my_window))
df.groupBy('goal').count().show()
df = df.filter(df.goal.isNotNull())

# Calcul de vitesse selon la distance entre des coordonnées et une coeifficent de transformation (Une coeifficent expérimentale est utilisée pour le test )
df = df.withColumn("vitesse",sqrt(pow(df.x-df.nxt_x,2)+pow(df.y-df.nxt_y,2)))
df = df.withColumn("vitesse",round(df["vitesse"]*30/500,2))
df = df.withColumn("total_goal",sum(df.goal).over(my_window))
df.show()

# Enregistrement dans un nouveau fichier json
df.write.json("file:///home/ymo/babyfoot.json",mode = 'overwrite')
exit()