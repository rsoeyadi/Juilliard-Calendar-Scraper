/*!
 * Easy Popup v0.0.5
 * https://github.com/viivue/easy-popup
 */
;(function(EasyPopup){
    /**
     * Private class Popup
     */
    class Popup{
        constructor(el, options){
            if(!el){
                console.warn('Init popup fail due to empty input!');
                return;
            }

            this.root = document.querySelector(':root');
            this.el = el;
            this.selector = 'data-easy-popup';
            this.attributes = {
                id: `${this.selector}-id`,
                title: `${this.selector}-title`,
                toggle: `${this.selector}-toggle`,
                mobileLayout: `${this.selector}-mobile`,
                theme: `${this.selector}-theme`,
                clickOutsideToClose: `${this.selector}-click-outside-to-close`
            };
            this.classes = {
                master: 'easy-popup-master',
                processed: 'easy-popup-enabled',
                triggerEnabled: 'easy-popup-trigger-enabled',
                content: 'easy-popup-content',
                outer: 'easy-popup',
                inner: 'easy-popup-inner',
                center: 'easy-popup-center',
                overflow: 'easy-popup-overflow',
                container: 'easy-popup-container',
                open: 'open',
                closeButton: 'easy-popup-close-button',
                mobileHeading: 'easy-popup-mobile-heading',
                hasMobileLayout: 'easy-popup-has-mobile-layout',
                ignoreClick: 'easy-popup-ignore-click',
            };
            this.innerHTML = this.el.innerHTML;
            this.isOpen = false;

            // options
            this.options = {
                ...{
                    id: this.uniqueId('easy-popup-'),
                    outerClass: '',
                    title: '',
                    closeButtonHTML: `<span><svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px" fill="#000000"><path d="M0 0h24v24H0z" fill="none"/><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg></span>`,
                    triggerSelector: '',
                    hasMobileLayout: false, // has mobile layout, false by default
                    theme: 'default',

                    keyboard: true, // option for closing the popup by keyboard (ESC)

                    clickOutsideToClose: true,

                    onClose: () => {
                    },
                    onOpen: () => {
                    }
                }, ...options
            };

            // get string options from attribute and js init
            this.id = this.el.getAttribute(this.selector) || this.options.id;
            this.title = this.el.getAttribute(this.attributes.title) || this.options.title;
            this.theme = this.el.getAttribute(this.attributes.theme) || this.options.theme;

            // get boolean options from attribute and js init
            this.isClickOutsideToClose = this.isBooleanOptionTrue(this.attributes.clickOutsideToClose, this.options.clickOutsideToClose);
            this.hasMobileLayout = this.isBooleanOptionTrue(this.attributes.mobileLayout, this.options.hasMobileLayout);

            this.closeButtonHTML = this.options.closeButtonHTML;
            this.masterContainer = document.querySelector(`.${this.classes.master}`);

            this.generateHTML();

            // assign triggers via a[href="#id"], [toggle="id"]
            let triggerSelector = `a[href="#${this.id}"], [${this.attributes.toggle}="${this.id}"]`;
            triggerSelector = this.options.triggerSelector ? `${this.options.triggerSelector}, ${triggerSelector}` : triggerSelector;
            document.querySelectorAll(triggerSelector).forEach(trigger => {
                trigger.classList.add(this.classes.triggerEnabled);
                trigger.addEventListener('click', e => {
                    e.preventDefault();
                    this.toggle();
                });
            });
        }

        isBooleanOptionTrue(attr, option){
            const attrValue = this.el.getAttribute(attr);
            return attrValue ? attrValue !== 'false' : option;
        }

        generateHTML(){
            // check flag
            if(this.el.classList.contains(this.classes.processed)) return;

            // relocate HTML to body tag
            if(!this.masterContainer){
                this.masterContainer = document.createElement('div');
                this.masterContainer.classList.add(this.classes.master);
            }
            document.querySelector('body').appendChild(this.masterContainer);
            this.masterContainer.appendChild(this.el);

            // inner
            this.inner = this.wrap(this.el);
            this.inner.classList.add(this.classes.inner);

            // add inner close button
            this.closeButton = document.createElement('button');
            this.closeButton.classList.add(this.classes.closeButton);
            this.closeButton.innerHTML = this.closeButtonHTML;
            this.closeButton.setAttribute(this.attributes.toggle, '');
            this.closeButton.addEventListener('click', () => this.close());
            this.inner.appendChild(this.closeButton);

            // container
            this.container = this.wrap(this.inner);
            this.container.classList.add(this.classes.container);

            // overflow
            this.overflow = this.wrap(this.container);
            this.overflow.classList.add(this.classes.overflow);

            // overflow > mobile heading
            this.mobileHeading = document.createElement('div');
            this.mobileHeading.classList.add(this.classes.mobileHeading);
            this.mobileHeading.innerHTML = `<div class="easy-popup-heading-inner">
            <div>${this.title}</div>
            <button class="${this.classes.closeButton} mobile" ${this.attributes.toggle}>${this.closeButtonHTML}</button>
            </div>`;
            this.overflow.appendChild(this.mobileHeading);

            // outer
            this.outer = this.wrap(this.overflow);
            this.outer.classList.add(this.classes.outer);
            if(this.options.outerClass) this.outer.classList.add(this.options.outerClass);
            if(this.hasMobileLayout) this.outer.classList.add(this.classes.hasMobileLayout);
            this.outer.setAttribute(this.attributes.id, this.id);

            // set theme
            this.outer.setAttribute(this.attributes.theme, this.theme);

            // close when click outside of content
            this.outer.addEventListener('click', e => {
                if(e.target.classList.contains(this.classes.ignoreClick)) return;
                if(this.isClickOutsideContent(e) && this.isClickOutsideToClose) this.close();
            });

            // close buttons on click
            this.outer.querySelectorAll('[data-easy-popup-toggle]').forEach(btn => {
                btn.addEventListener('click', () => this.close());
            });

            // add event listener when press ESC
            if(this.options.keyboard){
                document.addEventListener('keyup', (e) => {
                    if(this.isOpen && e.key === 'Escape'){
                        this.close();
                    }
                });
            }

            // done init
            this.el.classList.add(this.classes.processed, this.classes.content);
        }

        isClickOutsideContent(event){
            return !this.inner.contains(event.target) && !this.mobileHeading.contains(event.target);
        }

        open(){
            // check active popup
            if(window.EasyPopupData.active){
                EasyPopup.get(window.EasyPopupData.active).close();
            }

            // open
            window.EasyPopupData.active = this.id;
            this.outer.classList.add(this.classes.open);
            this.isOpen = true;
            this.root.classList.add('easy-popup-open');

            // prevent scroll > on
            this.root.style.paddingRight = `${this.getScrollbarWidth()}px`;
            this.root.style.overflow = `hidden`;

            // event
            if(typeof this.options.onOpen === 'function') this.options.onOpen(this);
        }

        close(){
            // close
            window.EasyPopupData.active = '';
            this.outer.classList.remove(this.classes.open);
            this.isOpen = false;
            this.root.classList.remove('easy-popup-open');

            // prevent scroll > off
            setTimeout(() => {
                // set close status when no popup is active
                if(!window.EasyPopupData.active){
                    this.root.style.paddingRight = ``;
                    this.root.style.overflow = ``;
                }

                // event
                if(typeof this.options.onClose === 'function') this.options.onClose(this);
            }, 300);
        }

        toggle(){
            this.isOpen ? this.close() : this.open();
        }

        /**
         * Wrap element
         * @param innerEl
         * @param outerEl
         * @returns {HTMLDivElement}
         */
        wrap(innerEl, outerEl = document.createElement('div')){
            innerEl.parentNode.insertBefore(outerEl, innerEl);
            outerEl.appendChild(innerEl);
            return outerEl;
        }

        /**
         * Get scrollbar width
         * https://stackoverflow.com/a/986977/6453822
         * @returns {number}
         */
        getScrollbarWidth(){
            // Creating invisible container
            const outer = document.createElement('div');
            outer.style.visibility = 'hidden';
            outer.style.overflow = 'scroll'; // forcing scrollbar to appear
            outer.style.msOverflowStyle = 'scrollbar'; // needed for WinJS apps
            document.body.appendChild(outer);

            // Creating inner element and placing it in the container
            const inner = document.createElement('div');
            outer.appendChild(inner);

            // Calculating difference between container's full width and the child width
            const scrollbarWidth = (outer.offsetWidth - inner.offsetWidth);

            // Removing temporary elements from the DOM
            outer.parentNode.removeChild(outer);

            return scrollbarWidth;
        }

        /**
         * Generate unique ID
         */
        uniqueId(prefix = ''){
            return prefix + (+new Date()).toString(16) +
                (Math.random() * 100000000 | 0).toString(16);
        }
    }


    /**
     * Private class Popup Controller
     */
    class PopupController{
        constructor(){
            this.active = '';
            this.popups = [];
        }

        add(popup){
            this.popups.push(popup);
        }

        get(id){
            return this.popups.filter(popup => popup.id === id)[0];
        }
    }

    /**
     * Public data
     * access via window.EasyPopupData
     */
    window.EasyPopupData = new PopupController();

    /**
     * Public methods
     */
    // init new popups
    EasyPopup.init = (selector = '[data-easy-popup]', options = {}) => {
        document.querySelectorAll(selector).forEach(el => window.EasyPopupData.add(new Popup(el, options)));
    };
    EasyPopup.init();

    // Get popup object by ID
    EasyPopup.get = id => window.EasyPopupData.get(id);


})(window.EasyPopup = window.EasyPopup || {});