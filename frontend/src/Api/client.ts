import axios from 'axios'


const client = axios.create({
  baseURL: '/api',
  withCredentials: true 

})



axios.interceptors.response.use(
    (response) => response,
    async (error) => {
        if(error.response?.status === 401){
            try{
                await axios.post('api/auth/ref' , {} , {withCredentials :true})
                return client(error.config)

            }catch{
                window.location.href ="/login"

            }
        }
         return Promise.reject(error)
    }

)

export default client

