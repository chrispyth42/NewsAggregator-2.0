// http://www.jtricks.com/javascript/blocks/showinghiding.html
function togglePageElementVisibility(what)  
{  
    var obj = typeof what == 'object'  
        ? what : document.getElementById(what);  
  
    if (obj.style.display == 'none')  
        obj.style.display = 'block';  
    else  
        obj.style.display = 'none';  
    return false;  
}  