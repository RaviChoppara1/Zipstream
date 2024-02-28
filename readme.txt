Zipstream:


      For the purpose of reducing Aircard data utilization and reducing AWS storage costs for the AID7 Site M2025 cameras, this Microservice automatically changes the Zipstream strength parameter on a scheduled basis for all production cameras.

   We intend to change the camera's zipstream strength from off to high or extrem at 9AM, and from high or extrem to off at 4PM

Key features :

1)Complete automation process
2)This code will change the zipstream settings as per cameras timezome
3)Initially Code will store the table data in Cache and then start exercuting
4) If devide is not in active, code will retry for two times
5) all these logs will upload to S3 with 30 days reytention period.


----------------------------------------------


Test Cameras:
http://10.76.12.152:10002 --CT
http://10.76.12.152:10003 --CT
http://10.76.12.152:10006 --CT
http://10.76.12.152:10008 --MT

--------------------------------------------------
note :
pip install boto3
pip install --upgrade boto3 botocore urllib3 pyopenssl
--------------------------------------------------
23/02/24
Total M2025 Camera in Production : 3473
                             CT : 1442
                             ET : 1242
                             PT : 509
                             MT  : 243
                           No data : 33
                            UTC : 3 (test)
                            IST :1 (test)
---------------------------------------------------------

9AM - Zipstream : OFF to High/Extrem
4PM - Zipstream : High/Extream to OFF
------------------------------------------------------------

	

1)14:00 UTC :python3 main.py ravichoppara 12Ravi@#34 profit_db view_camentity3 --strength 50 --query_type ET --database_endpoint provigil-dev-db-cluster.cluster-cmo78nhwb6in.us-east-1.rds.amazonaws.com --database_port 3306

2)15:00 UTC :python3 main.py ravichoppara 12Ravi@#34 profit_db view_camentity3 --strength 50 --query_type CT --database_endpoint provigil-dev-db-cluster.cluster-cmo78nhwb6in.us-east-1.rds.amazonaws.com --database_port 3306

3)16:00 UTC :python3 main.py ravichoppara 12Ravi@#34 profit_db view_camentity3 --strength 50 --query_type MT --database_endpoint provigil-dev-db-cluster.cluster-cmo78nhwb6in.us-east-1.rds.amazonaws.com --database_port 3306

4)17:00 UTC :python3 main.py ravichoppara 12Ravi@#34 profit_db view_camentity3 --strength 50 --query_type PT --database_endpoint provigil-dev-db-cluster.cluster-cmo78nhwb6in.us-east-1.rds.amazonaws.com --database_port 3306

	

5)21:00 UTC :python3 main.py ravichoppara 12Ravi@#34 profit_db view_camentity3 --strength off --query_type ET --database_endpoint provigil-dev-db-cluster.cluster-cmo78nhwb6in.us-east-1.rds.amazonaws.com --database_port 3306

6)22:00 UTC:python3 main.py ravichoppara 12Ravi@#34 profit_db view_camentity3 --strength off --query_type CT --database_endpoint provigil-dev-db-cluster.cluster-cmo78nhwb6in.us-east-1.rds.amazonaws.com --database_port 3306

7)23:00 UTC:python3 main.py ravichoppara 12Ravi@#34 profit_db view_camentity3 --strength off --query_type MT --database_endpoint provigil-dev-db-cluster.cluster-cmo78nhwb6in.us-east-1.rds.amazonaws.com --database_port 3306

8)23:59 UTC:python3 main.py ravichoppara 12Ravi@#34 profit_db view_camentity3 --strength off --query_type PT --database_endpoint provigil-dev-db-cluster.cluster-cmo78nhwb6in.us-east-1.rds.amazonaws.com --database_port 3306




---------------------------
note :
pip install boto3
pip install --upgrade boto3 botocore urllib3 pyopenssl
