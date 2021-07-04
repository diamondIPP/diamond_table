
  // When the user clicks on the button, toggle between hiding and showing the dropdown content
  function f0() { document.getElementById("drop0").classList.toggle("show"); }
  function f1() { document.getElementById("drop1").classList.toggle("show"); }
  function f2() { document.getElementById("drop2").classList.toggle("show"); }
  function f3() { document.getElementById("drop3").classList.toggle("show"); }
  function f4() { document.getElementById("drop4").classList.toggle("show"); }
  function f5() { document.getElementById("drop5").classList.toggle("show"); }

  // Close the dropdown if the user clicks outside of it
  window.onclick = function(e){
    if (!e.target.matches('.dropbtn')) {
      var drop0 = document.getElementById("drop0");
      if (drop0.classList.contains('show')) { drop0.classList.remove('show'); }
      var drop1 = document.getElementById("drop1");
      if (drop1.classList.contains('show')) { drop1.classList.remove('show'); }
      var drop2 = document.getElementById("drop2");
      if (drop2.classList.contains('show')) { drop2.classList.remove('show'); }
      var drop3 = document.getElementById("drop3");
      if (drop3.classList.contains('show')) { drop3.classList.remove('show'); }
      var drop4 = document.getElementById("drop4");
      if (drop4.classList.contains('show')) { drop4.classList.remove('show'); }
      var drop5 = document.getElementById("drop5");
      if (drop5.classList.contains('show')) { drop5.classList.remove('show'); }
    }
  }

// show home page
function load_home() {
document.getElementById("content").innerHTML='<object type="text/html" data="Overview/2019.html" ></object>';
}

$(function(){
  $("#nav-placeholder").load("/psi2/content/nav.html");
});
