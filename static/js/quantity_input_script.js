/* 
* Disable +/- buttons outside 1-99 range.
* If no size is passed to the function, the parameter will have a value of undefined by default,
* which prevents any errors 
*/
function handleEnableDisable(itemId, size) {
    if (size) {
        var currentValue = parseInt($(`.size_${itemId}_${size}`).val());
    } else {
        var currentValue = parseInt($(`.id_qty_${itemId}`).val());
    }
    let minusDisabled = currentValue < 2;
    let plusDisabled = currentValue > 98;
    if (size) {
        $(`.decrement-size_${itemId}_${size}`).prop('disabled', minusDisabled);
        $(`.increment-size_${itemId}_${size}`).prop('disabled', plusDisabled);
    } else {
        $(`.decrement-qty_${itemId}`).prop('disabled', minusDisabled);
        $(`.increment-qty_${itemId}`).prop('disabled', plusDisabled);
    }
}

// Ensure proper enabling/disabling of all inputs on page load
let allQtyInputs = $('.qty_input');
for(let i = 0; i < allQtyInputs.length; i++){
    let itemId = $(allQtyInputs[i]).data('item_id');
    var size = $(allQtyInputs[i]).data('size');
    handleEnableDisable(itemId, size);
}

// Check enable/disable every time the input is changed
$('.qty_input').change(function() {
    let itemId = $(this).data('item_id');
    var size = $(this).data('size');
    handleEnableDisable(itemId, size);
});

// Increment quantity
$('.increment-qty').click(function(e) {
    e.preventDefault();
    var itemId = $(this).data('item_id');
    var size = $(this).data('size');
    let closestInput = $(this).closest('.input-group').find('.qty_input')[0];
    if (size) {
        var allQuantityInputs = $(`.input-group-${itemId} input[data-size='${size}']`);
    } else {
        var allQuantityInputs = $(`.input-group-${itemId} input[name='quantity']`);
    }
    let currentValue = parseInt($(closestInput).val());
    $(allQuantityInputs).val(currentValue + 1);
    handleEnableDisable(itemId, size);
});

// Decrement quantity
$('.decrement-qty').click(function(e) {
    e.preventDefault();
    var itemId = $(this).data('item_id');
    var size = $(this).data('size');
    let closestInput = $(this).closest('.input-group').find('.qty_input')[0];
    if (size) {
        var allQuantityInputs = $(`.input-group-${itemId} input[data-size='${size}']`);
    } else {
        var allQuantityInputs = $(`.input-group-${itemId} input[name='quantity']`);
    }
    let currentValue = parseInt($(closestInput).val());
    $(allQuantityInputs).val(currentValue - 1);
    handleEnableDisable(itemId, size);
});