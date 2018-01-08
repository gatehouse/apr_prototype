from django import forms

class GetPortInfo(forms.Form):
    port = forms.SlugField(label = 'Port')

class SubmitPortInfo(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__()
        elements = kwargs.get('elements', None)
        if elements:
            a = elements.split(',')
            for i, e in enumerate(a):
                print("ELEM %s" % e)
                self.add_field(i, e)

        port = kwargs.get('port', None)
        if port:
            print("PORT %s" % port)
            self.fields['port'] = forms.CharField(widget = forms.HiddenInput(), initial=port)

    def add_field(self, index, field):
        self.fields['re_%s' % field] = forms.CharField(label=field)

    imo = forms.DecimalField(max_value = 9999999, decimal_places = 0, label = 'IMO')
    
