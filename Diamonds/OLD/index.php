<!DOCTYPE html>
<!--dorfer@phys.ethz.ch-->
<html>

<head>
<style>
table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
}
th{
    padding: 5px;
    text-align: center;
}
td{
    padding: 5px;
    text-align: left;
}

</style>
</head>
<body>

<!--table header-->
<br>
<table style="width:70%">
  <tr>
    <th>Number</th>
    <th>Diamond</th>
    <th>Beam Tests</th>
    <th>CCD Results</th>
    <th>Comments</th>
  </tr>
<?php
$count = 0;
$dirs = array_diff(scandir("."), array('.', '..'));
foreach ($dirs as $value){
  if(is_dir($value)){
    $count += 1;

    //get config file information
    $conf_txt = "";
    $conf_file = $value . "/Comments/comment.txt";
    $conf = fopen($conf_file, "r");
    if ($conf == false){
      $conf_txt = "Could not find a comment.txt file!";
    }else{
      while(!feof($conf)){
        $conf_txt = $conf_txt . fgets($conf) . "<br>";
      }
      fclose($conf);
    }
    //end get config file information

    echo "  <tr> \n";
      echo "    <td> $count </td> \n";
      echo "    <td> $value </td> \n";
      echo "    <td> unknown </td> \n";
      echo "    <td> unknown </td> \n";
      echo "    <td> $conf_txt </td> \n";
    echo "  </tr>\n";
   }
}
?>

</table>

</body>
</html> 
