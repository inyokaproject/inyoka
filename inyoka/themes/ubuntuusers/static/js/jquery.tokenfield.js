(function($){
$.token_field = function(input, options) {
	var $input = $(input);
	var $hidden_field = $('<input type="hidden"></input>');
	var token_list = [];
	var token_elements_list = [];
	$hidden_field.attr("name",$input.attr("name"));
	createTokens($input.val());
	$hidden_field.val($input.val());
	$input.val("");
	$input.removeAttr("name");
	$input.addClass(options.searchInputClass);
	$hidden_field.insertAfter($input);
	
	
	function createTokens(data) {
		var tokens = data.split(options.splitToken);
		for(token in tokens) {
			if (tokens[token].replace(/^\s+|\s+$/g, '') != '') {
				$token = $(createToken(tokens[token]));
				token_list.push(tokens[token]);
				token_elements_list.push($token);
				$token.insertBefore($input);
			}
		}
	};
	
	function createToken(token) {
		var $token = $("<span class=" + options.tokenClass + ">" + token + "</span>");
		$token.append($('<span class="tf_tok_delete">&nbsp;&nbsp;&nbsp;</span>').click(function () {
			delindex = token_list.indexOf($token.text().replace(/^\s+|\s+$/g, ''));
			token_list.splice(delindex, 1);
			token_elements_list.splice(delindex, 1);
			$token.remove();
			$hidden_field.val(token_list.join(options.splitToken));
		}));
		return $token;
	};
	this.handleItemSelect = function() {
		createTokens($input.val());
		$input.val("");
		$hidden_field.val(token_list.join(options.splitToken));
	};
	this.handleBlur = function() {
		if($input.val() != "") {
			createTokens($input.val());
			$input.val("");
			$hidden_field.val(token_list.join(options.splitToken));
		}
	};
	this.handleDelete = function() {
		if(token_list.length > 0) {
			token_list.pop();
			token_elements_list.pop().remove();
			$hidden_field.val(token_list.join(options.splitToken));
		}
	};
};
$.fn.token_field = function(url, options, data) {
	options = options || {};
	
	options.splitToken = options.splitToken || ";";
	options.tokenClass = options.tokenClass || "tf_token";
	
	this.each(function() {
		var input = this;
		var token_field = new $.token_field(input, options);
		options.onItemSelect = function() {
			token_field.handleItemSelect();
		}
		options.onDelete = function() {
			token_field.handleDelete();
		}
		options.onBlur = function() {
			setTimeout(function() {
				token_field.handleBlur();
			},100);
		}
		options.onSplitToken = function() {
			token_field.handleBlur();
		}
		$(input).autocomplete(url, options, data);
	});
};
})(jQuery);
